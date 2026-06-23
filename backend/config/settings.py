"""
Neel AI — Application Settings.

All runtime-configurable values live here.  They can be overridden via
environment variables or a ``.env`` file.  Values that MUST NOT be
configurable (sovereign email) live in ``governance.py``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration loaded from environment / .env file.

    Environment variable prefix: ``NEEL_``
    Example:  ``NEEL_OLLAMA_BASE_URL=http://localhost:11434``
    """

    model_config = SettingsConfigDict(
        env_prefix="NEEL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────
    app_name: str = "Neel AI"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # ── Server ───────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8001

    # ── CORS ─────────────────────────────────────────────────────────
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
        ]
    )

    # ── Ollama ───────────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.2:3b"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_timeout: float = 120.0
    ollama_max_tokens: int = 2048

    # ── LM Studio ────────────────────────────────────────────────────
    lmstudio_base_url: str = "http://localhost:1234/v1"
    lmstudio_default_model: str = "default"
    lmstudio_timeout: float = 120.0

    # ── ChromaDB ─────────────────────────────────────────────────────
    chroma_host: str = "localhost"
    chroma_port: int = 8100
    chroma_default_collection: str = "neel_memory"

    # ── JWT / Auth ───────────────────────────────────────────────────
    jwt_secret_key: str = "neel-ai-change-me-in-production-2026"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_minutes: int = 10080  # 7 days

    # ── SQLite Audit DB ──────────────────────────────────────────────
    sqlite_db_path: str = "data/db/neel_audit.db"

    # ── File Upload ──────────────────────────────────────────────────
    upload_dir: str = "data/uploads"
    max_upload_size_mb: int = 50

    # ── Trident Engine ───────────────────────────────────────────────
    trident_max_iterations: int = 10
    trident_sandbox_timeout: int = 30  # seconds per tool call
    trident_sandbox_dir: str = "data/sandbox"

    # ── Derived helpers ──────────────────────────────────────────────

    @property
    def upload_path(self) -> Path:
        """Resolved upload directory as a Path object."""
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def db_path(self) -> Path:
        """Resolved SQLite database path."""
        p = Path(self.sqlite_db_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def max_upload_bytes(self) -> int:
        """Max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    # ── Compatibility aliases (used by module routers) ───────────

    @property
    def default_model(self) -> str:
        """Alias for ollama_default_model."""
        return self.ollama_default_model

    @property
    def trident_task_timeout(self) -> int:
        """Alias for trident_sandbox_timeout."""
        return self.trident_sandbox_timeout

    @property
    def audit_db_path(self) -> str:
        """Alias for sqlite_db_path."""
        return self.sqlite_db_path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached singleton of the application settings.

    Using ``lru_cache`` ensures the settings are read once from the
    environment and then reused for the lifetime of the process.
    """
    return Settings()
