"""
Neel AI — Main Application Entry Point
========================================
FastAPI application that ties together all modules:
LLM integration, memory/RAG, functional modules, Trident engine,
sovereign dashboard, and governance enforcement.

Launch: uvicorn main:app --reload --port 8001
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.governance import GovernanceConfig, GOVERNANCE, SOVEREIGN_EMAIL
from config.settings import get_settings


# ── Lifespan ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()

    # Startup
    print("=" * 60)
    print(f"  🔱 {GOVERNANCE.system_name} v{GOVERNANCE.version}")
    print(f"  Sovereign: {GOVERNANCE.sovereign_email}")
    print(f"  Model: {settings.default_model}")
    print(f"  Ollama: {settings.ollama_base_url}")
    print(f"  ChromaDB: {settings.chroma_host}:{settings.chroma_port}")
    print(f"  Backend: http://{settings.host}:{settings.port}")
    print("=" * 60)

    # Create necessary directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.trident_sandbox_dir, exist_ok=True)
    os.makedirs(os.path.dirname(settings.audit_db_path) or "data/db", exist_ok=True)

    # Initialize audit database
    from sovereign.audit import get_audit_logger, AuditAction
    audit = get_audit_logger()
    await audit.log(
        action=AuditAction.SYSTEM_STARTUP,
        actor_email=GOVERNANCE.sovereign_email,
        resource="system",
        details={"model": settings.default_model, "timestamp": datetime.utcnow().isoformat()},
    )

    yield

    # Shutdown
    await audit.log(
        action=AuditAction.SYSTEM_SHUTDOWN,
        actor_email=GOVERNANCE.sovereign_email,
        resource="system",
        details={"timestamp": datetime.utcnow().isoformat()},
    )
    print("🔱 Neel AI shutting down...")


# ── App Creation ────────────────────────────────────────────

app = FastAPI(
    title="Neel AI",
    description="Sovereign Intelligence Suite — A privacy-first, locally-hosted AI platform",
    version=GOVERNANCE.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS Middleware ─────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://frontend:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id", "X-Request-Time"],
)


# ── Health Check ────────────────────────────────────────────

@app.get("/api/health", tags=["System"])
async def health_check():
    """System health check endpoint used by Docker health checks."""
    settings = get_settings()

    # Check Ollama connectivity
    ollama_status = "unknown"
    try:
        from llm.ollama_client import get_ollama_client
        client = get_ollama_client()
        ok = await client.health_check()
        ollama_status = "connected" if ok else "disconnected"
    except Exception:
        ollama_status = "disconnected"

    # Check ChromaDB connectivity
    chroma_status = "unknown"
    try:
        from memory.chroma_client import ChromaManager
        chroma = ChromaManager()
        heartbeat = await chroma.heartbeat()
        chroma_status = "connected" if heartbeat else "disconnected"
    except Exception:
        chroma_status = "disconnected"

    return {
        "status": "healthy",
        "system": GOVERNANCE.system_name,
        "version": GOVERNANCE.version,
        "sovereign": GOVERNANCE.sovereign_email,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "ollama": ollama_status,
            "chromadb": chroma_status,
        },
        "config": {
            "default_model": settings.default_model,
            "ollama_url": settings.ollama_base_url,
        },
    }


# ── Register Routers ───────────────────────────────────────

from llm.router import router as llm_router
from memory.router import router as memory_router
from auth.middleware import router as auth_router
from sovereign.router import router as sovereign_router
from modules.coders.router import router as coders_router
from modules.social_media.router import router as social_router
from modules.marketing.router import router as marketing_router
from modules.students.router import router as students_router
from modules.research.router import router as research_router
from trident.router import router as trident_router

app.include_router(llm_router)
app.include_router(memory_router)
app.include_router(auth_router)
app.include_router(sovereign_router)
app.include_router(coders_router)
app.include_router(social_router)
app.include_router(marketing_router)
app.include_router(students_router)
app.include_router(research_router)
app.include_router(trident_router)


# ── Global Exception Handler ──────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return a clean JSON response."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__,
        },
    )


# ── Root ───────────────────────────────────────────────────

@app.get("/", tags=["System"])
async def root():
    """Root endpoint — system info."""
    return {
        "name": GOVERNANCE.system_name,
        "version": GOVERNANCE.version,
        "docs": "/docs",
        "health": "/api/health",
    }
