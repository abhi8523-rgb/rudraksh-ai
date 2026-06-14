"""
Rudraksh AI — Auth & RBAC Tests
=================================
Tests for authentication, RBAC enforcement, and governance constraints.
"""

import pytest
from config.governance import GovernanceConfig


class TestGovernance:
    """Tests for the governance hardcoding — CRITICAL."""

    def test_sovereign_email_hardcoded(self):
        """The sovereign email must ALWAYS be abhi8523@gmail.com."""
        config = GovernanceConfig()
        assert config.SOVEREIGN_ADMIN_EMAIL == "abhi8523@gmail.com"

    def test_system_name(self):
        """System name must be Rudraksh AI."""
        config = GovernanceConfig()
        assert config.SYSTEM_NAME == "Rudraksh AI"

    def test_sovereign_permissions(self):
        """Sovereign must have all permissions."""
        config = GovernanceConfig()
        permissions = config.SOVEREIGN_PERMISSIONS
        assert "system:admin" in permissions
        assert "models:manage" in permissions
        assert "audit:read" in permissions
        assert "shivoham:execute" in permissions

    def test_report_recipient(self):
        """All reports must route to the sovereign email."""
        config = GovernanceConfig()
        assert config.REPORT_RECIPIENT == config.SOVEREIGN_ADMIN_EMAIL


class TestRBAC:
    """Tests for Role-Based Access Control."""

    def test_import(self):
        """Test RBAC module can be imported."""
        from auth.rbac import RoleChecker
        assert RoleChecker is not None

    def test_role_checker_creation(self):
        """Test RoleChecker can be created with allowed roles."""
        from auth.rbac import RoleChecker
        checker = RoleChecker(allowed_roles=["sovereign_administrator"])
        assert checker is not None

    def test_sovereign_role_exists(self):
        """Test that the sovereign role is defined."""
        config = GovernanceConfig()
        assert config.SOVEREIGN_ROLE == "sovereign_administrator"
