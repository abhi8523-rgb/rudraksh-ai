"""
Neel AI — Auth & RBAC Tests
=================================
Tests for authentication, RBAC enforcement, and governance constraints.
"""

import pytest
from config.governance import GovernanceConfig, GOVERNANCE, SOVEREIGN_EMAIL, Role, Permission


class TestGovernance:
    """Tests for the governance hardcoding — CRITICAL."""

    def test_sovereign_email_hardcoded(self):
        """The sovereign email must ALWAYS be abhi8523@gmail.com."""
        assert SOVEREIGN_EMAIL == "abhi8523@gmail.com"
        assert GOVERNANCE.sovereign_email == "abhi8523@gmail.com"

    def test_system_name(self):
        """System name must be Neel AI."""
        assert GOVERNANCE.system_name == "Neel AI"

    def test_sovereign_has_all_permissions(self):
        """Sovereign must have ALL permissions."""
        perms = GovernanceConfig.get_permissions(Role.SOVEREIGN)
        assert Permission.MANAGE_GOVERNANCE in perms
        assert Permission.MANAGE_MODELS in perms
        assert Permission.VIEW_AUDIT_LOGS in perms
        assert Permission.EXECUTE_Trident in perms
        assert Permission.QUERY_LLM in perms

    def test_is_sovereign(self):
        """is_sovereign must return True for the hardcoded email."""
        assert GOVERNANCE.is_sovereign("abhi8523@gmail.com")
        assert GOVERNANCE.is_sovereign("ABHI8523@GMAIL.COM")  # case insensitive
        assert not GOVERNANCE.is_sovereign("other@example.com")

    def test_governance_immutable(self):
        """Governance values cannot be changed at runtime."""
        config = GovernanceConfig(sovereign_email="hacker@evil.com")
        # __post_init__ should override back to the real email
        assert config.sovereign_email == "abhi8523@gmail.com"

    def test_role_hierarchy(self):
        """Role hierarchy must be correct."""
        assert GovernanceConfig.role_rank(Role.SOVEREIGN) == 0
        assert GovernanceConfig.role_rank(Role.ADMIN) == 1
        assert GovernanceConfig.role_rank(Role.VIEWER) == 4

    def test_role_at_least(self):
        """role_at_least must correctly compare roles."""
        assert GovernanceConfig.role_at_least(Role.SOVEREIGN, Role.ADMIN)
        assert GovernanceConfig.role_at_least(Role.ADMIN, Role.ADMIN)
        assert not GovernanceConfig.role_at_least(Role.VIEWER, Role.ADMIN)


class TestRBAC:
    """Tests for Role-Based Access Control."""

    def test_import(self):
        """Test RBAC module can be imported."""
        from auth.rbac import get_current_user, require_permission
        assert get_current_user is not None
        assert require_permission is not None

    def test_viewer_permissions(self):
        """Viewers should only have VIEW_DASHBOARD."""
        perms = GovernanceConfig.get_permissions(Role.VIEWER)
        assert Permission.VIEW_DASHBOARD in perms
        assert Permission.MANAGE_MODELS not in perms

    def test_operator_permissions(self):
        """Operators should have module access."""
        perms = GovernanceConfig.get_permissions(Role.OPERATOR)
        assert Permission.USE_MODULES in perms
        assert Permission.INGEST_DOCUMENTS in perms
        assert Permission.MANAGE_MODELS not in perms
