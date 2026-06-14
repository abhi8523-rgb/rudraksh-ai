"""
Rudraksh AI — Coders Module API Routes
=======================================
Endpoints for code generation, refactoring, documentation, and security scanning.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional

from modules.coders.prompts import get_prompt
from llm.ollama_client import OllamaClient
from llm.streaming import create_sse_stream
from auth.middleware import get_current_user_optional
from config.settings import get_settings

router = APIRouter(prefix="/api/coders", tags=["Coders"])


# ── Request Schemas ─────────────────────────────────────────

class CodeGenerateRequest(BaseModel):
    language: str = Field(..., description="Programming language", examples=["python", "javascript"])
    task: str = Field(..., description="Description of what to generate", min_length=5)
    context: Optional[str] = Field(None, description="Additional context or constraints")
    model: Optional[str] = Field(None, description="Override default model")
    stream: bool = Field(True, description="Stream the response")

class CodeRefactorRequest(BaseModel):
    language: str = Field(..., description="Programming language")
    code: str = Field(..., description="Code to refactor", min_length=10)
    focus_areas: Optional[str] = Field(None, description="Areas to focus on (e.g., performance, readability)")
    constraints: Optional[str] = Field(None, description="Constraints to respect")
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class CodeDocumentRequest(BaseModel):
    language: str = Field(..., description="Programming language")
    code: str = Field(..., description="Code to document", min_length=10)
    doc_style: Optional[str] = Field(None, description="Documentation style (e.g., Google, NumPy, JSDoc)")
    audience: Optional[str] = Field(None, description="Target audience (e.g., beginner, senior dev)")
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class SecurityScanRequest(BaseModel):
    language: str = Field(..., description="Programming language")
    code: str = Field(..., description="Code to scan", min_length=10)
    scan_depth: Optional[str] = Field("thorough", description="Scan depth: quick, standard, thorough")
    app_type: Optional[str] = Field(None, description="Application type (e.g., web API, CLI, library)")
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class CodeResponse(BaseModel):
    action: str
    content: str
    model_used: str
    tokens_used: Optional[int] = None


# ── Helper ──────────────────────────────────────────────────

async def _process_code_request(
    action: str,
    params: dict,
    model: Optional[str],
    stream: bool,
):
    """Process a code module request with optional streaming."""
    settings = get_settings()
    client = OllamaClient()
    
    try:
        prompts = get_prompt(action, **params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    use_model = model or settings.default_model
    
    messages = [
        {"role": "system", "content": prompts["system"]},
        {"role": "user", "content": prompts["user"]},
    ]
    
    if stream:
        async def generate():
            async for chunk in client.chat_stream(model=use_model, messages=messages):
                yield chunk
        
        return create_sse_stream(generate())
    else:
        response = await client.chat(model=use_model, messages=messages)
        return CodeResponse(
            action=action,
            content=response.get("message", {}).get("content", ""),
            model_used=use_model,
            tokens_used=response.get("eval_count"),
        )


# ── Endpoints ───────────────────────────────────────────────

@router.post("/generate", summary="Generate code from description")
async def generate_code(request: CodeGenerateRequest):
    """Generate production-quality code from a natural language description."""
    params = {
        "language": request.language,
        "task": request.task,
        "context": request.context or "Not specified",
    }
    return await _process_code_request("generate", params, request.model, request.stream)


@router.post("/refactor", summary="Refactor existing code")
async def refactor_code(request: CodeRefactorRequest):
    """Analyze and refactor code for improved quality, readability, and performance."""
    params = {
        "language": request.language,
        "code": request.code,
        "focus_areas": request.focus_areas or "General improvements",
        "constraints": request.constraints or "None",
    }
    return await _process_code_request("refactor", params, request.model, request.stream)


@router.post("/document", summary="Generate documentation for code")
async def document_code(request: CodeDocumentRequest):
    """Generate comprehensive documentation including docstrings and API references."""
    params = {
        "language": request.language,
        "code": request.code,
        "doc_style": request.doc_style or "Standard for the language",
        "audience": request.audience or "Developers",
    }
    return await _process_code_request("document", params, request.model, request.stream)


@router.post("/scan", summary="Scan code for security vulnerabilities")
async def scan_code(request: SecurityScanRequest):
    """Perform static security analysis to identify vulnerabilities and risks."""
    params = {
        "language": request.language,
        "code": request.code,
        "scan_depth": request.scan_depth or "thorough",
        "app_type": request.app_type or "General application",
    }
    return await _process_code_request("security_scan", params, request.model, request.stream)
