"""
Neel AI — Governance Configuration.

IMMUTABLE sovereign administrator configuration.
This file defines the absolute, hardcoded governance hierarchy.
The Sovereign Administrator email MUST NOT be loaded from environment
variables or any external configuration source.

Sovereignty Principle:
    The system recognises exactly ONE immutable Sovereign Administrator
    whose identity is baked into the source code itself. This identity
    cannot be overridden, impersonated, or revoked at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, unique
from typing import Final, FrozenSet


# ──────────────────────────────────────────────────────────────────────
#  HARDCODED SOVEREIGN — DO NOT MODIFY
# ──────────────────────────────────────────────────────────────────────
SOVEREIGN_EMAIL: Final[str] = "abhi8523@gmail.com"
"""The one and only Sovereign Administrator email.  Immutable."""


@unique
class Role(StrEnum):
    """
    Hierarchical role taxonomy.

    Sovereign > Admin > Operator > Analyst > Viewer
    Each higher role inherits every permission of the roles below it.
    """

    SOVEREIGN = "sovereign"
    ADMIN = "admin"
    OPERATOR = "operator"
    ANALYST = "analyst"
    VIEWER = "viewer"


# Ordered from highest to lowest privilege
ROLE_HIERARCHY: Final[list[Role]] = [
    Role.SOVEREIGN,
    Role.ADMIN,
    Role.OPERATOR,
    Role.ANALYST,
    Role.VIEWER,
]


@unique
class Permission(StrEnum):
    """Fine-grained permissions assigned to roles."""

    # Sovereign-only
    MANAGE_GOVERNANCE = "manage_governance"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_USERS = "manage_users"

    # Admin+
    MANAGE_MODELS = "manage_models"
    MANAGE_MEMORY = "manage_memory"
    EXECUTE_TRIDENT = "execute_trident"

    # Operator+
    INGEST_DOCUMENTS = "ingest_documents"
    USE_MODULES = "use_modules"

    # Analyst+
    QUERY_LLM = "query_llm"
    QUERY_MEMORY = "query_memory"

    # Viewer
    VIEW_DASHBOARD = "view_dashboard"


# ──────────────────────────────────────────────────────────────────────
#  Role → Permission mapping
# ──────────────────────────────────────────────────────────────────────
_ROLE_PERMISSIONS: Final[dict[Role, FrozenSet[Permission]]] = {
    Role.VIEWER: frozenset({
        Permission.VIEW_DASHBOARD,
    }),
    Role.ANALYST: frozenset({
        Permission.VIEW_DASHBOARD,
        Permission.QUERY_LLM,
        Permission.QUERY_MEMORY,
    }),
    Role.OPERATOR: frozenset({
        Permission.VIEW_DASHBOARD,
        Permission.QUERY_LLM,
        Permission.QUERY_MEMORY,
        Permission.INGEST_DOCUMENTS,
        Permission.USE_MODULES,
    }),
    Role.ADMIN: frozenset({
        Permission.VIEW_DASHBOARD,
        Permission.QUERY_LLM,
        Permission.QUERY_MEMORY,
        Permission.INGEST_DOCUMENTS,
        Permission.USE_MODULES,
        Permission.MANAGE_MODELS,
        Permission.MANAGE_MEMORY,
        Permission.EXECUTE_TRIDENT,
    }),
    Role.SOVEREIGN: frozenset(Permission),  # ALL permissions
}


@dataclass(frozen=True, slots=True)
class GovernanceConfig:
    """
    Immutable governance configuration for the Neel AI system.

    This is a frozen dataclass — once created, it cannot be mutated.
    The ``sovereign_email`` field is always hardcoded to the canonical value
    regardless of what the caller passes (the ``__post_init__`` hook
    enforces this).
    """

    sovereign_email: str = field(default=SOVEREIGN_EMAIL)
    role_hierarchy: tuple[Role, ...] = field(
        default_factory=lambda: tuple(ROLE_HIERARCHY)
    )
    system_name: str = "Neel AI"
    version: str = "1.0.0"

    def __post_init__(self) -> None:
        """Enforce immutable sovereign identity regardless of init args."""
        # frozen dataclass requires object.__setattr__ for post-init overrides
        if self.sovereign_email != SOVEREIGN_EMAIL:
            object.__setattr__(self, "sovereign_email", SOVEREIGN_EMAIL)

    # ── Query helpers ────────────────────────────────────────────────

    def is_sovereign(self, email: str) -> bool:
        """Check whether the given email matches the Sovereign Administrator."""
        return email.strip().lower() == SOVEREIGN_EMAIL.lower()

    @staticmethod
    def get_permissions(role: Role) -> FrozenSet[Permission]:
        """Return the permission set for a given role."""
        return _ROLE_PERMISSIONS.get(role, frozenset())

    @staticmethod
    def has_permission(role: Role, permission: Permission) -> bool:
        """Check whether a role possesses a specific permission."""
        return permission in _ROLE_PERMISSIONS.get(role, frozenset())

    @staticmethod
    def role_rank(role: Role) -> int:
        """
        Return a numeric rank for the role (lower number = higher privilege).
        Sovereign = 0, Viewer = 4.
        """
        try:
            return ROLE_HIERARCHY.index(role)
        except ValueError:
            return len(ROLE_HIERARCHY)  # unknown roles rank lowest

    @staticmethod
    def role_at_least(user_role: Role, required_role: Role) -> bool:
        """Return True if *user_role* is equal to or higher than *required_role*."""
        return GovernanceConfig.role_rank(user_role) <= GovernanceConfig.role_rank(required_role)


# ──────────────────────────────────────────────────────────────────────
#  Module-level singleton — importers get a ready-to-use config.
# ──────────────────────────────────────────────────────────────────────
GOVERNANCE = GovernanceConfig()
