"""
Rudraksh AI — Audit Logger.

Provides persistent, tamper-evident audit logging using SQLite (aiosqlite).
Every significant action in the system is recorded with:
  - Timestamp
  - Actor identity (user_id, email, role)
  - Action type
  - Resource affected
  - Request details
  - Outcome (success/failure)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import StrEnum, unique
from pathlib import Path
from typing import Any, Optional

import aiosqlite

from config.settings import Settings, get_settings

logger = logging.getLogger("rudraksh.sovereign.audit")


@unique
class AuditAction(StrEnum):
    """Categories of auditable actions."""

    # Auth
    LOGIN = "auth.login"
    LOGOUT = "auth.logout"
    REGISTER = "auth.register"
    PASSWORD_CHANGE = "auth.password_change"
    TOKEN_REFRESH = "auth.token_refresh"

    # LLM
    LLM_CHAT = "llm.chat"
    LLM_GENERATE = "llm.generate"
    LLM_EMBED = "llm.embed"
    MODEL_PULL = "llm.model_pull"
    MODEL_DELETE = "llm.model_delete"

    # Memory
    MEMORY_QUERY = "memory.query"
    MEMORY_INGEST = "memory.ingest"
    COLLECTION_CREATE = "memory.collection_create"
    COLLECTION_DELETE = "memory.collection_delete"

    # Modules
    MODULE_EXECUTE = "module.execute"

    # Shivoham
    SHIVOHAM_EXECUTE = "shivoham.execute"
    SHIVOHAM_TOOL_CALL = "shivoham.tool_call"

    # Admin
    USER_CREATE = "admin.user_create"
    CONFIG_CHANGE = "admin.config_change"

    # System
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    HEALTH_CHECK = "system.health_check"


_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,
    action      TEXT    NOT NULL,
    actor_id    TEXT,
    actor_email TEXT,
    actor_role  TEXT,
    resource    TEXT,
    details     TEXT,
    outcome     TEXT    NOT NULL DEFAULT 'success',
    ip_address  TEXT,
    user_agent  TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action    ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_actor     ON audit_log(actor_id);
"""


class AuditLogger:
    """
    Async audit logger backed by SQLite.

    Usage::

        audit = get_audit_logger()
        await audit.log(
            action=AuditAction.LOGIN,
            actor_id="abc123",
            actor_email="user@example.com",
            actor_role="viewer",
            resource="auth",
            details={"method": "password"},
        )
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._db_path = str(self._settings.db_path)
        self._initialised = False

    async def _ensure_db(self) -> None:
        """Create the audit table if it doesn't exist."""
        if self._initialised:
            return

        # Ensure parent directory exists
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(_CREATE_TABLE_SQL)
            await db.commit()

        self._initialised = True
        logger.info("Audit database initialised at %s", self._db_path)

    async def log(
        self,
        action: AuditAction | str,
        actor_id: str | None = None,
        actor_email: str | None = None,
        actor_role: str | None = None,
        resource: str | None = None,
        details: dict[str, Any] | None = None,
        outcome: str = "success",
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> int:
        """
        Write an audit log entry.

        Returns the row ID of the inserted record.
        """
        await self._ensure_db()

        now = datetime.now(timezone.utc).isoformat()
        details_json = json.dumps(details, default=str) if details else None

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO audit_log
                    (timestamp, action, actor_id, actor_email, actor_role,
                     resource, details, outcome, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    str(action),
                    actor_id,
                    actor_email,
                    actor_role,
                    resource,
                    details_json,
                    outcome,
                    ip_address,
                    user_agent,
                ),
            )
            await db.commit()
            row_id = cursor.lastrowid

        logger.debug(
            "Audit [%s] actor=%s resource=%s outcome=%s",
            action,
            actor_email or actor_id or "system",
            resource,
            outcome,
        )
        return row_id

    async def query_logs(
        self,
        action: str | None = None,
        actor_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Query audit logs with optional filters.

        Args:
            action: Filter by action type.
            actor_id: Filter by actor.
            since: ISO timestamp lower bound.
            until: ISO timestamp upper bound.
            limit: Max results.
            offset: Pagination offset.

        Returns:
            List of audit log dicts.
        """
        await self._ensure_db()

        conditions: list[str] = []
        params: list[Any] = []

        if action:
            conditions.append("action = ?")
            params.append(action)
        if actor_id:
            conditions.append("actor_id = ?")
            params.append(actor_id)
        if since:
            conditions.append("timestamp >= ?")
            params.append(since)
        if until:
            conditions.append("timestamp <= ?")
            params.append(until)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        sql = f"""
            SELECT id, timestamp, action, actor_id, actor_email, actor_role,
                   resource, details, outcome, ip_address, user_agent
            FROM audit_log
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()

        results = []
        for row in rows:
            entry = dict(row)
            if entry.get("details"):
                try:
                    entry["details"] = json.loads(entry["details"])
                except json.JSONDecodeError:
                    pass
            results.append(entry)

        return results

    async def count_logs(
        self,
        action: str | None = None,
        since: str | None = None,
    ) -> int:
        """Count audit log entries with optional filters."""
        await self._ensure_db()

        conditions: list[str] = []
        params: list[Any] = []

        if action:
            conditions.append("action = ?")
            params.append(action)
        if since:
            conditions.append("timestamp >= ?")
            params.append(since)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                f"SELECT COUNT(*) FROM audit_log WHERE {where_clause}",
                params,
            )
            row = await cursor.fetchone()
            return row[0] if row else 0


# ──────────────────────────────────────────────────────────────────────
#  Singleton
# ──────────────────────────────────────────────────────────────────────

_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Return the module-level audit logger singleton."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
