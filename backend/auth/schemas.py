"""
Neel AI — Auth Pydantic Schemas.

Request / response models for authentication and user identity.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from config.governance import Role, Permission


# ──────────────────────────────────────────────────────────────────────
#  User identity
# ──────────────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    """Payload for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=128)
    role: Role = Role.VIEWER


class UserIdentity(BaseModel):
    """
    Represents an authenticated user within the system.

    Populated from the JWT token claims and carried through the
    request lifecycle via ``Depends(get_current_user)``.
    """

    user_id: str
    email: str
    display_name: str = ""
    role: Role = Role.VIEWER
    permissions: frozenset[Permission] = Field(default_factory=frozenset)
    is_sovereign: bool = False

    model_config = {"arbitrary_types_allowed": True}

    @property
    def is_admin_or_above(self) -> bool:
        """Return True if the user is Admin or Sovereign."""
        return self.role in {Role.SOVEREIGN, Role.ADMIN}


# ──────────────────────────────────────────────────────────────────────
#  Token schemas
# ──────────────────────────────────────────────────────────────────────


class TokenPayload(BaseModel):
    """Claims encoded inside the JWT."""

    sub: str  # user_id
    email: str
    display_name: str = ""
    role: Role = Role.VIEWER
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Returned to the client after successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(
        ..., description="Access token lifetime in seconds"
    )
    user: UserIdentity


class TokenRefreshRequest(BaseModel):
    """Payload for refreshing an access token."""

    refresh_token: str


# ──────────────────────────────────────────────────────────────────────
#  Login request
# ──────────────────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    """Credentials submitted for authentication."""

    email: EmailStr
    password: str = Field(..., min_length=1)


# ──────────────────────────────────────────────────────────────────────
#  Password change
# ──────────────────────────────────────────────────────────────────────


class PasswordChangeRequest(BaseModel):
    """Request to change the current user's password."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
