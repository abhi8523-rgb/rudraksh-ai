"""
Rudraksh AI — System Metrics.

Collects runtime metrics about the Rudraksh AI system:
  - CPU / memory usage
  - LLM provider status
  - ChromaDB stats
  - Uptime
  - Request counts (from audit logs)
"""

from __future__ import annotations

import logging
import os
import platform
import time
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger("rudraksh.sovereign.metrics")

# Startup timestamp
_START_TIME = time.time()


class SystemInfo(BaseModel):
    """Static system information."""
    platform: str
    python_version: str
    cpu_count: int
    hostname: str


class ResourceUsage(BaseModel):
    """Current resource utilization."""
    cpu_percent: float
    memory_total_mb: float
    memory_used_mb: float
    memory_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float


class ProviderStatus(BaseModel):
    """Status of an LLM provider."""
    name: str
    healthy: bool
    url: str


class MetricsSnapshot(BaseModel):
    """Complete system metrics snapshot."""
    timestamp: str
    uptime_seconds: float
    system: SystemInfo
    resources: ResourceUsage
    providers: list[ProviderStatus]
    memory_store: dict[str, Any]
    audit_counts: dict[str, int]


class SystemMetrics:
    """Collects and returns system metrics."""

    @staticmethod
    def get_system_info() -> SystemInfo:
        """Return static system information."""
        return SystemInfo(
            platform=platform.platform(),
            python_version=platform.python_version(),
            cpu_count=os.cpu_count() or 1,
            hostname=platform.node(),
        )

    @staticmethod
    def get_resource_usage() -> ResourceUsage:
        """
        Return current resource utilisation.

        Uses os-level calls to avoid requiring psutil as a dependency.
        Falls back to safe defaults on Windows or when info is unavailable.
        """
        try:
            import shutil

            # Disk usage
            disk = shutil.disk_usage(".")
            disk_total_gb = disk.total / (1024 ** 3)
            disk_used_gb = disk.used / (1024 ** 3)
            disk_percent = (disk.used / disk.total) * 100 if disk.total else 0.0
        except Exception:
            disk_total_gb = 0.0
            disk_used_gb = 0.0
            disk_percent = 0.0

        # Memory — try to get from OS
        memory_total = 16.0 * 1024  # fallback: 16GB in MB
        memory_used = 0.0
        memory_percent = 0.0

        try:
            if platform.system() == "Windows":
                import ctypes

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                memory_total = stat.ullTotalPhys / (1024 ** 2)
                memory_used = memory_total - (stat.ullAvailPhys / (1024 ** 2))
                memory_percent = stat.dwMemoryLoad
            else:
                # Linux / macOS — read /proc/meminfo
                with open("/proc/meminfo") as f:
                    meminfo = {}
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val = parts[1].strip().split()[0]
                            meminfo[key] = int(val)

                    total_kb = meminfo.get("MemTotal", 0)
                    avail_kb = meminfo.get("MemAvailable", 0)
                    memory_total = total_kb / 1024
                    memory_used = (total_kb - avail_kb) / 1024
                    memory_percent = (
                        ((total_kb - avail_kb) / total_kb * 100) if total_kb else 0.0
                    )
        except Exception:
            pass

        # CPU percent — simple load average approximation
        cpu_percent = 0.0
        try:
            if hasattr(os, "getloadavg"):
                load1, _, _ = os.getloadavg()
                cpu_count = os.cpu_count() or 1
                cpu_percent = (load1 / cpu_count) * 100
        except Exception:
            pass

        return ResourceUsage(
            cpu_percent=round(cpu_percent, 1),
            memory_total_mb=round(memory_total, 1),
            memory_used_mb=round(memory_used, 1),
            memory_percent=round(memory_percent, 1),
            disk_total_gb=round(disk_total_gb, 1),
            disk_used_gb=round(disk_used_gb, 1),
            disk_percent=round(disk_percent, 1),
        )

    @staticmethod
    def get_uptime() -> float:
        """Return seconds since the process started."""
        return time.time() - _START_TIME

    @staticmethod
    async def get_provider_statuses() -> list[ProviderStatus]:
        """Check health of all LLM providers."""
        from config.settings import get_settings
        from llm.ollama_client import get_ollama_client
        from llm.lmstudio_client import get_lmstudio_client

        settings = get_settings()
        ollama = get_ollama_client()
        lmstudio = get_lmstudio_client()

        statuses = []

        ollama_ok = await ollama.health_check()
        statuses.append(
            ProviderStatus(
                name="ollama",
                healthy=ollama_ok,
                url=settings.ollama_base_url,
            )
        )

        lmstudio_ok = await lmstudio.health_check()
        statuses.append(
            ProviderStatus(
                name="lmstudio",
                healthy=lmstudio_ok,
                url=settings.lmstudio_base_url,
            )
        )

        return statuses

    @staticmethod
    def get_memory_store_stats() -> dict[str, Any]:
        """Get ChromaDB statistics."""
        try:
            from memory.chroma_client import get_chroma_client

            chroma = get_chroma_client()
            healthy = chroma.health_check()
            if healthy:
                collections = chroma.list_collections()
                total_docs = sum(chroma.count(c) for c in collections)
                return {
                    "healthy": True,
                    "collections": len(collections),
                    "total_documents": total_docs,
                }
            return {"healthy": False, "collections": 0, "total_documents": 0}
        except Exception:
            return {"healthy": False, "collections": 0, "total_documents": 0}

    @classmethod
    async def snapshot(cls) -> MetricsSnapshot:
        """Capture a complete metrics snapshot."""
        providers = await cls.get_provider_statuses()

        # Audit counts
        audit_counts: dict[str, int] = {}
        try:
            from sovereign.audit import get_audit_logger

            audit = get_audit_logger()
            audit_counts["total"] = await audit.count_logs()
            audit_counts["last_24h"] = await audit.count_logs(
                since=datetime.now(timezone.utc)
                .replace(hour=0, minute=0, second=0)
                .isoformat()
            )
        except Exception:
            audit_counts = {"total": 0, "last_24h": 0}

        return MetricsSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            uptime_seconds=round(cls.get_uptime(), 1),
            system=cls.get_system_info(),
            resources=cls.get_resource_usage(),
            providers=providers,
            memory_store=cls.get_memory_store_stats(),
            audit_counts=audit_counts,
        )
