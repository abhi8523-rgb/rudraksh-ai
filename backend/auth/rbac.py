"""
Neel AI — Role-Based Access Control (RBAC).

Provides FastAPI dependency callables that:
  1. Extract and validate the JWT from the ``Authorization`` header.
  2. Build a ``UserIdentity`` from token claims.
  3. Enforce role and permission requirements on individual routes.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from auth.schemas import TokenPayload, TokenResponse, UserIdentity
from config.governance import (
    SOVEREIGN_EMAIL,
    GovernanceConfig,
    Permission,
    Role,
)
from config.settings import Settings, get_settings

logger = logging.getLogger("neel.auth")

# ──────────────────────────────────────────────────────────────────────
#  Password hashing
# ──────────────────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_bearer_scheme = HTTPBearer(auto_error=False)

# ──────────────────────────────────────────────────────────────────────
#  In-memory user store (production would use a real DB)
# ──────────────────────────────────────────────────────────────────────
_USERS_DB: dict[str, dict] = {}
_USERS_FILE = Path("data/db/users.json")


def _load_users() -> None:
    """Load users from persistent JSON file on startup."""
    global _USERS_DB
    if _USERS_FILE.exists():
        try:
            _USERS_DB = json.loads(_USERS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            _USERS_DB = {}


def _save_users() -> None:
    """Persist user database to disk."""
    _USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _USERS_FILE.write_text(
        json.dumps(_USERS_DB, indent=2, default=str), encoding="utf-8"
    )


def _user_id_from_email(email: str) -> str:
    """Deterministic user ID derived from email."""
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()[:16]


# Bootstrap the sovereign user at import time
_load_users()
_sovereign_id = _user_id_from_email(SOVEREIGN_EMAIL)
if _sovereign_id not in _USERS_DB:
    _USERS_DB[_sovereign_id] = {
        "user_id": _sovereign_id,
        "email": SOVEREIGN_EMAIL,
        "display_name": "Sovereign Administrator",
        "role": Role.SOVEREIGN.value,
        "password_hash": pwd_context.hash("neel2026"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_users()


# ──────────────────────────────────────────────────────────────────────
#  User CRUD helpers
# ──────────────────────────────────────────────────────────────────────


def create_user(
    email: str,
    password: str,
    display_name: str,
    role: Role = Role.VIEWER,
) -> dict:
    """Create a new user.  Raises ValueError if already exists."""
    uid = _user_id_from_email(email)
    if uid in _USERS_DB:
        raise ValueError(f"User with email {email} already exists")
    user_record = {
        "user_id": uid,
        "email": email.lower().strip(),
        "display_name": display_name,
        "role": role.value,
        "password_hash": pwd_context.hash(password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _USERS_DB[uid] = user_record
    _save_users()
    return user_record


def authenticate_user(email: str, password: str) -> dict | None:
    """Verify credentials.  Returns user record or None."""
    uid = _user_id_from_email(email)
    user = _USERS_DB.get(uid)
    if user is None:
        return None
    if not pwd_context.verify(password, user["password_hash"]):
        return None
    return user


def get_user_by_id(user_id: str) -> dict | None:
    return _USERS_DB.get(user_id)


def change_password(user_id: str, new_password: str) -> None:
    """Update a user's password hash."""
    if user_id not in _USERS_DB:
        raise ValueError("User not found")
    _USERS_DB[user_id]["password_hash"] = pwd_context.hash(new_password)
    _save_users()


# ──────────────────────────────────────────────────────────────────────
#  JWT creation
# ──────────────────────────────────────────────────────────────────────


def create_access_token(
    user: dict, settings: Settings | None = None
) -> str:
    """Create a signed JWT access token."""
    settings = settings or get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["user_id"],
        "email": user["email"],
        "display_name": user.get("display_name", ""),
        "role": user["role"],
        "iat": now,
        "exp": now
        + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    user: dict, settings: Settings | None = None
) -> str:
    """Create a signed JWT refresh token."""
    settings = settings or get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["user_id"],
        "email": user["email"],
        "type": "refresh",
        "iat": now,
        "exp": now
        + timedelta(minutes=settings.jwt_refresh_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_token_response(user: dict, settings: Settings | None = None) -> TokenResponse:
    """Build a full token response for a user."""
    settings = settings or get_settings()
    governance = GovernanceConfig()

    access = create_access_token(user, settings)
    refresh = create_refresh_token(user, settings)
    role = Role(user["role"])

    identity = UserIdentity(
        user_id=user["user_id"],
        email=user["email"],
        display_name=user.get("display_name", ""),
        role=role,
        permissions=governance.get_permissions(role),
        is_sovereign=governance.is_sovereign(user["email"]),
    )
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=identity,
    )


# ──────────────────────────────────────────────────────────────────────
#  JWT validation → UserIdentity
# ──────────────────────────────────────────────────────────────────────


def _decode_token(token: str, settings: Settings | None = None) -> dict:
    """Decode and validate a JWT.  Raises HTTPException on failure."""
    settings = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> UserIdentity:
    """
    FastAPI dependency that extracts the current user from the JWT.

    Usage::

        @router.get("/me")
        async def me(user: UserIdentity = Depends(get_current_user)):
            return user
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token(credentials.credentials, settings)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected access token",
        )

    role = Role(payload.get("role", Role.VIEWER.value))
    governance = GovernanceConfig()

    return UserIdentity(
        user_id=payload["sub"],
        email=payload.get("email", ""),
        display_name=payload.get("display_name", ""),
        role=role,
        permissions=governance.get_permissions(role),
        is_sovereign=governance.is_sovereign(payload.get("email", "")),
    )


# ──────────────────────────────────────────────────────────────────────
#  Role / Permission guards (used as Depends)
# ──────────────────────────────────────────────────────────────────────


def require_role(minimum_role: Role) -> Callable:
    """
    Return a FastAPI dependency that enforces a minimum role level.

    Usage::

        @router.post("/admin-action", dependencies=[Depends(require_role(Role.ADMIN))])
        async def admin_action(): ...
    """

    async def _guard(
        user: UserIdentity = Depends(get_current_user),
    ) -> UserIdentity:
        from config.governance import ROLE_HIERARCHY

        try:
            user_rank = ROLE_HIERARCHY.index(user.role)
            required_rank = ROLE_HIERARCHY.index(minimum_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unknown role",
            )

        if user_rank > required_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role: requires {minimum_role.value}, you have {user.role.value}",
            )

        return user

    return _guard


def require_permission(permission: Permission) -> Callable:
    """
    Return a FastAPI dependency that enforces a specific permission.

    Usage::

        @router.delete("/collection", dependencies=[Depends(require_permission(Permission.MANAGE_MEMORY))])
        async def delete_collection(): ...
    """

    async def _guard(
        user: UserIdentity = Depends(get_current_user),
    ) -> UserIdentity:
        if permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission.value}",
            )
        return user

    return _guard
