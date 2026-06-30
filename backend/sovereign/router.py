"""
Neel AI — Sovereign Router.

Administrative endpoints restricted to the Sovereign Administrator
and Admin roles:
  - System metrics & dashboard
  - Audit log viewing
  - Governance information
  - User management overview
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from auth.rbac import get_current_user, require_role, require_permission
from auth.schemas import UserIdentity
from config.governance import (
    GOVERNANCE,
    SOVEREIGN_EMAIL,
    GovernanceConfig,
    Permission,
    Role,
    ROLE_HIERARCHY,
)
from config.settings import get_settings
from sovereign.audit import AuditAction, get_audit_logger
from sovereign.metrics import MetricsSnapshot, SystemMetrics

logger = logging.getLogger("neel.sovereign.router")

router = APIRouter(prefix="/api/v1/sovereign", tags=["Sovereign Administration"])


# ──────────────────────────────────────────────────────────────────────
#  Schemas
# ──────────────────────────────────────────────────────────────────────


class GovernanceInfo(BaseModel):
    """Public governance information."""
    system_name: str
    version: str
    sovereign_email: str
    role_hierarchy: list[str]
    roles: dict[str, list[str]]


class AuditLogEntry(BaseModel):
    """A single audit log entry."""
    id: int
    timestamp: str
    action: str
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    actor_role: Optional[str] = None
    resource: Optional[str] = None
    details: Any = None
    outcome: str = "success"
    ip_address: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Paginated audit log response."""
    entries: list[AuditLogEntry]
    total: int
    limit: int
    offset: int


# ──────────────────────────────────────────────────────────────────────
#  Endpoints
# ──────────────────────────────────────────────────────────────────────


@router.get(
    "/governance",
    response_model=GovernanceInfo,
    summary="View governance configuration",
)
async def get_governance(
    user: UserIdentity = Depends(get_current_user),
) -> GovernanceInfo:
    """Return the system's governance configuration and role hierarchy."""
    governance = GOVERNANCE

    roles_perms: dict[str, list[str]] = {}
    for role in Role:
        perms = governance.get_permissions(role)
        roles_perms[role.value] = sorted(p.value for p in perms)

    return GovernanceInfo(
        system_name=governance.system_name,
        version=governance.version,
        sovereign_email=SOVEREIGN_EMAIL,
        role_hierarchy=[r.value for r in ROLE_HIERARCHY],
        roles=roles_perms,
    )


@router.get(
    "/metrics",
    response_model=MetricsSnapshot,
    summary="System metrics snapshot",
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def get_metrics() -> MetricsSnapshot:
    """
    Capture a comprehensive system metrics snapshot.

    Includes CPU, memory, disk, provider health, ChromaDB stats, and audit counts.
    Only accessible to Admin and Sovereign.
    """
    return await SystemMetrics.snapshot()


@router.get(
    "/audit",
    response_model=AuditLogResponse,
    summary="Query audit logs",
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def query_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action type"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    since: Optional[str] = Query(None, description="ISO timestamp lower bound"),
    until: Optional[str] = Query(None, description="ISO timestamp upper bound"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> AuditLogResponse:
    """
    Query the audit log with optional filters.

    Only the Sovereign can access audit logs.
    """
    audit = get_audit_logger()

    entries = await audit.query_logs(
        action=action,
        actor_id=actor_id,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )

    total = await audit.count_logs(action=action, since=since)

    return AuditLogResponse(
        entries=[AuditLogEntry(**e) for e in entries],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/audit/actions",
    response_model=list[str],
    summary="List available audit action types",
    dependencies=[Depends(require_permission(Permission.VIEW_AUDIT_LOGS))],
)
async def list_audit_actions() -> list[str]:
    """Return all defined audit action types."""
    return [a.value for a in AuditAction]


@router.get(
    "/health",
    summary="Detailed system health check",
)
async def detailed_health(
    user: UserIdentity = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Detailed health check including all subsystem statuses.
    """
    from llm.ollama_client import get_ollama_client
    from llm.lmstudio_client import get_lmstudio_client
    from memory.chroma_client import get_chroma_client

    settings = get_settings()

    ollama_ok = await get_ollama_client().health_check()
    lmstudio_ok = await get_lmstudio_client().health_check()
    chroma_ok = get_chroma_client().health_check()

    all_healthy = ollama_ok and chroma_ok  # LM Studio is optional

    return {
        "status": "healthy" if all_healthy else "degraded",
        "subsystems": {
            "ollama": {
                "healthy": ollama_ok,
                "url": settings.ollama_base_url,
            },
            "lmstudio": {
                "healthy": lmstudio_ok,
                "url": settings.lmstudio_base_url,
                "note": "Optional — system works without LM Studio",
            },
            "chromadb": {
                "healthy": chroma_ok,
                "host": settings.chroma_host,
                "port": settings.chroma_port,
            },
        },
        "uptime_seconds": round(SystemMetrics.get_uptime(), 1),
    }


@router.get(
    "/config",
    summary="View runtime configuration",
    dependencies=[Depends(require_role(Role.SOVEREIGN))],
)
async def get_runtime_config() -> dict[str, Any]:
    """
    View the current runtime configuration.

    Sovereign-only.  Sensitive values (JWT secret) are masked.
    """
    settings = get_settings()

    config = {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_default_model": settings.ollama_default_model,
        "ollama_embed_model": settings.ollama_embed_model,
        "lmstudio_base_url": settings.lmstudio_base_url,
        "chroma_host": settings.chroma_host,
        "chroma_port": settings.chroma_port,
        "chroma_default_collection": settings.chroma_default_collection,
        "jwt_algorithm": settings.jwt_algorithm,
        "jwt_secret_key": "***MASKED***",
        "jwt_access_token_expire_minutes": settings.jwt_access_token_expire_minutes,
        "max_upload_size_mb": settings.max_upload_size_mb,
        "trident_max_iterations": settings.trident_max_iterations,
        "Trident_sandbox_timeout": settings.Trident_sandbox_timeout,
    }

    return config
