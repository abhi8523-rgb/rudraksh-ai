"""
Neel AI — Authentication & Authorisation Package.

Provides JWT-based authentication, RBAC middleware, and Pydantic schemas
for user identity management.
"""

from auth.schemas import TokenPayload, TokenResponse, UserIdentity, UserCreate
from auth.rbac import require_role, require_permission, get_current_user
from auth.middleware import AuthMiddleware

__all__ = [
    "TokenPayload",
    "TokenResponse",
    "UserIdentity",
    "UserCreate",
    "require_role",
    "require_permission",
    "get_current_user",
    "AuthMiddleware",
]
