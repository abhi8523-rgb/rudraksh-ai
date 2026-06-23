"""
Neel AI — Auth Middleware.

Provides an ASGI middleware that performs lightweight JWT validation
on every request (except explicitly excluded paths).
Also exposes an auth router for login / register / refresh / me endpoints.
"""

from __future__ import annotations

import logging
import time
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from auth.rbac import (
    authenticate_user,
    change_password,
    create_token_response,
    create_user,
    get_current_user,
    get_user_by_id,
    require_role,
    _decode_token,
)
from auth.schemas import (
    LoginRequest,
    PasswordChangeRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserIdentity,
)
from config.governance import Role, SOVEREIGN_EMAIL
from config.settings import get_settings

logger = logging.getLogger("neel.auth.middleware")

# ──────────────────────────────────────────────────────────────────────
#  ASGI Middleware — lightweight request logging & timing
# ──────────────────────────────────────────────────────────────────────

# Paths that skip authentication entirely
_PUBLIC_PATHS: frozenset[str] = frozenset({
    "/health",
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
})


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Lightweight ASGI middleware that:
      - Logs request method, path, and response time.
      - Skips auth validation for public paths.
      - Adds ``X-Request-Time`` header to every response.

    Full JWT validation is handled at the route level via
    ``Depends(get_current_user)`` — this middleware only provides
    request-level observability.
    """

    def __init__(self, app, public_paths: Sequence[str] | None = None):
        super().__init__(app)
        self.public_paths = frozenset(public_paths) if public_paths else _PUBLIC_PATHS

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()

        # Attach timing info to request state for downstream use
        request.state.request_start = start

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-Time"] = f"{elapsed_ms:.2f}ms"

        logger.debug(
            "%s %s → %d (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        return response


# ──────────────────────────────────────────────────────────────────────
#  Auth Router — /api/v1/auth/*
# ──────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> UserIdentity | None:
    """
    Like ``get_current_user`` but returns None when no token is present.
    Useful for module endpoints that work both authenticated and public.
    """
    if credentials is None:
        return None
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(body: UserCreate) -> TokenResponse:
    """
    Register a new user account.

    - The first user to register gets the Viewer role by default.
    - The Sovereign account (abhi8523@gmail.com) is pre-seeded and
      cannot be re-registered.
    """
    if body.email.lower().strip() == SOVEREIGN_EMAIL.lower():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sovereign account is pre-configured and cannot be registered.",
        )

    # Non-sovereign users can only self-register as Viewer
    effective_role = Role.VIEWER

    try:
        user_record = create_user(
            email=body.email,
            password=body.password,
            display_name=body.display_name,
            role=effective_role,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return create_token_response(user_record)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive tokens",
)
async def login(body: LoginRequest) -> TokenResponse:
    """Authenticate with email and password.  Returns access + refresh tokens."""
    user_record = authenticate_user(body.email, body.password)
    if user_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return create_token_response(user_record)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(body: TokenRefreshRequest) -> TokenResponse:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    settings = get_settings()
    payload = _decode_token(body.refresh_token, settings)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected refresh token",
        )

    user_record = get_user_by_id(payload["sub"])
    if user_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    return create_token_response(user_record)


@router.get(
    "/me",
    response_model=UserIdentity,
    summary="Get current user profile",
)
async def me(user: UserIdentity = Depends(get_current_user)) -> UserIdentity:
    """Return the authenticated user's identity and permissions."""
    return user


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
)
async def change_password_route(
    body: PasswordChangeRequest,
    user: UserIdentity = Depends(get_current_user),
) -> None:
    """Change the current user's password.  Requires the current password."""
    user_record = authenticate_user(user.email, body.current_password)
    if user_record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )
    change_password(user.user_id, body.new_password)


@router.post(
    "/create-user",
    response_model=UserIdentity,
    status_code=status.HTTP_201_CREATED,
    summary="Admin: create a user with a specific role",
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def admin_create_user(body: UserCreate) -> UserIdentity:
    """
    Create a user with an arbitrary role.

    Only Admins and Sovereign can invoke this.  The Sovereign role
    itself cannot be assigned to new users.
    """
    if body.role == Role.SOVEREIGN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The Sovereign role cannot be assigned to other users",
        )

    try:
        user_record = create_user(
            email=body.email,
            password=body.password,
            display_name=body.display_name,
            role=body.role,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    from config.governance import GovernanceConfig
    governance = GovernanceConfig()

    return UserIdentity(
        user_id=user_record["user_id"],
        email=user_record["email"],
        display_name=user_record["display_name"],
        role=Role(user_record["role"]),
        permissions=governance.get_permissions(Role(user_record["role"])),
        is_sovereign=False,
    )
