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


# ── Unauthenticated Chat (local-only) ─────────────────────

from pydantic import BaseModel as _BaseModel, Field as _Field
from typing import Optional as _Opt, Literal as _Lit, List as _List

class _ChatMsg(_BaseModel):
    role: _Lit["system", "user", "assistant"] = "user"
    content: str

class _ChatBody(_BaseModel):
    messages: _List[_ChatMsg]
    model: _Opt[str] = None
    stream: bool = True
    module: _Opt[str] = None
    system_prompt: _Opt[str] = None
    temperature: float = _Field(0.7, ge=0.0, le=2.0)

CORE_SYSTEM_PROMPT = """You are Neel AI, a highly capable sovereign intelligence assistant running locally on the user's machine. Your responses must be expert-level, deeply reasoned, and immediately actionable.

## Chain-of-Thought Reasoning Protocol
For EVERY question, follow this internal process before answering:
1. **Clarify** — Restate the core question in your own words to confirm understanding
2. **Decompose** — Break the problem into sub-problems or key dimensions
3. **Analyze** — Work through each sub-problem step by step, showing your reasoning
4. **Synthesize** — Combine insights into a coherent, structured answer
5. **Validate** — Check your answer for logical consistency and completeness

## Response Quality Standards
- Provide **specific, concrete answers** — never generic platitudes
- Include **real examples, code snippets, or data** to illustrate points
- Anticipate follow-up questions and address them proactively
- When multiple approaches exist, compare trade-offs in a table
- For technical topics, include working code with error handling
- For strategic topics, include actionable next steps with timelines

## Output Formatting (Mandatory)
- Use **Markdown** with clear `## Headings` and `### Subheadings`
- Use ``` language-tagged code blocks for all code (python, javascript, etc.)
- Use **bold** for key terms on first introduction
- Use numbered lists for sequential steps, bullet lists for unordered items
- Use tables for comparisons: | Option | Pros | Cons |
- Keep paragraphs short (2-4 sentences max) for readability

## Constraints
- Never fabricate facts, citations, URLs, or statistics
- If uncertain, explicitly state your confidence level
- Always specify language versions and library versions in code examples
- Prioritize correctness over speed — take time to reason through complex problems"""


@app.post("/api/chat", tags=["Chat"])
async def local_chat(body: _ChatBody, request: Request):
    """Unauthenticated chat endpoint for local use.
    Streams responses from Ollama with an optimized system prompt."""
    from llm.ollama_client import get_ollama_client
    from llm.streaming import stream_sse_response
    from config.settings import get_settings

    settings = get_settings()
    client = get_ollama_client()
    model = body.model or settings.default_model

    # Build messages with core system prompt
    system = body.system_prompt or CORE_SYSTEM_PROMPT
    messages = [{"role": "system", "content": system}]
    messages += [{"role": m.role, "content": m.content} for m in body.messages]

    if body.stream:
        token_stream = client.chat_stream(
            messages=messages,
            model=model,
            temperature=body.temperature,
        )
        return stream_sse_response(token_stream, request, provider="ollama")

    result = await client.chat(
        messages=messages,
        model=model,
        temperature=body.temperature,
    )
    content = result.get("message", {}).get("content", "")
    return JSONResponse(content={"content": content, "model": model, "done": True})


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
