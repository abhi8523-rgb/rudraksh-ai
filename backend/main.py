"""
Rudraksh AI — Main Application Entry Point
============================================
FastAPI application that ties together all modules:
LLM integration, memory/RAG, functional modules, Shivoham engine,
sovereign dashboard, and governance enforcement.

Launch: uvicorn main:app --reload --port 8000
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.governance import GovernanceConfig
from config.settings import get_settings


# ── Lifespan ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    governance = GovernanceConfig()
    
    # Startup
    print("=" * 60)
    print(f"  🔱 {governance.SYSTEM_NAME} v{governance.GOVERNANCE_VERSION}")
    print(f"  Sovereign: {governance.SOVEREIGN_ADMIN_EMAIL}")
    print(f"  Model: {settings.default_model}")
    print(f"  Ollama: {settings.ollama_base_url}")
    print(f"  ChromaDB: {settings.chroma_host}:{settings.chroma_port}")
    print("=" * 60)
    
    # Create necessary directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.shivoham_sandbox_dir, exist_ok=True)
    os.makedirs(os.path.dirname(settings.audit_db_path), exist_ok=True)
    
    # Initialize audit database
    from sovereign.audit import AuditLogger
    audit = AuditLogger()
    await audit.initialize()
    await audit.log_event(
        event_type="system_start",
        user_email=governance.SOVEREIGN_ADMIN_EMAIL,
        details={"model": settings.default_model, "timestamp": datetime.utcnow().isoformat()},
    )
    
    yield
    
    # Shutdown
    await audit.log_event(
        event_type="system_shutdown",
        user_email=governance.SOVEREIGN_ADMIN_EMAIL,
        details={"timestamp": datetime.utcnow().isoformat()},
    )
    print("🔱 Rudraksh AI shutting down...")


# ── App Creation ────────────────────────────────────────────

app = FastAPI(
    title="Rudraksh AI",
    description="Sovereign Intelligence Suite — A privacy-first, locally-hosted AI platform",
    version="1.0.0",
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
    expose_headers=["X-Request-Id"],
)


# ── Health Check ────────────────────────────────────────────

@app.get("/api/health", tags=["System"])
async def health_check():
    """System health check endpoint used by Docker health checks."""
    settings = get_settings()
    governance = GovernanceConfig()
    
    # Check Ollama connectivity
    ollama_status = "unknown"
    try:
        from llm.ollama_client import OllamaClient
        client = OllamaClient()
        models = await client.list_models()
        ollama_status = "connected" if models is not None else "error"
    except Exception:
        ollama_status = "disconnected"
    
    # Check ChromaDB connectivity  
    chroma_status = "unknown"
    try:
        from memory.chroma_client import ChromaManager
        chroma = ChromaManager()
        heartbeat = await chroma.heartbeat()
        chroma_status = "connected" if heartbeat else "error"
    except Exception:
        chroma_status = "disconnected"
    
    return {
        "status": "healthy",
        "system": governance.SYSTEM_NAME,
        "version": governance.GOVERNANCE_VERSION,
        "sovereign": governance.SOVEREIGN_ADMIN_EMAIL,
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
from shivoham.router import router as shivoham_router

app.include_router(llm_router)
app.include_router(memory_router)
app.include_router(auth_router)
app.include_router(sovereign_router)
app.include_router(coders_router)
app.include_router(social_router)
app.include_router(marketing_router)
app.include_router(students_router)
app.include_router(research_router)
app.include_router(shivoham_router)


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


# ── Root Redirect ──────────────────────────────────────────

@app.get("/", tags=["System"])
async def root():
    """Root endpoint — redirects to API documentation."""
    governance = GovernanceConfig()
    return {
        "name": governance.SYSTEM_NAME,
        "version": governance.GOVERNANCE_VERSION,
        "docs": "/docs",
        "health": "/api/health",
    }
