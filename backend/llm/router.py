"""
Rudraksh AI — LLM Router.

Unified API router for interacting with LLM providers (Ollama & LM Studio).
Provides endpoints for:
  - Chat completions (streaming & non-streaming)
  - Text generation
  - Embeddings
  - Model management
  - Provider health checks
"""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from auth.rbac import get_current_user, require_permission
from auth.schemas import UserIdentity
from config.governance import Permission
from config.models import (
    MODEL_REGISTRY,
    ModelConfig,
    ModelProvider,
    get_model_config,
    list_models,
)
from llm.ollama_client import OllamaClient, get_ollama_client
from llm.lmstudio_client import LMStudioClient, get_lmstudio_client
from llm.streaming import stream_sse_response

logger = logging.getLogger("rudraksh.llm.router")

router = APIRouter(prefix="/api/v1/llm", tags=["LLM"])


# ──────────────────────────────────────────────────────────────────────
#  Request / Response Schemas
# ──────────────────────────────────────────────────────────────────────


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""
    role: Literal["system", "user", "assistant"] = "user"
    content: str


class ChatRequest(BaseModel):
    """Request body for chat completions."""
    messages: list[ChatMessage]
    model: Optional[str] = None
    provider: Literal["ollama", "lmstudio"] = "ollama"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=32768)
    system_prompt: Optional[str] = None
    stream: bool = False


class GenerateRequest(BaseModel):
    """Request body for raw text generation."""
    prompt: str
    model: Optional[str] = None
    provider: Literal["ollama", "lmstudio"] = "ollama"
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=32768)
    system_prompt: Optional[str] = None
    stream: bool = False


class EmbedRequest(BaseModel):
    """Request body for embedding generation."""
    input: str | list[str]
    model: Optional[str] = None


class ChatResponse(BaseModel):
    """Non-streaming chat completion response."""
    content: str
    model: str
    provider: str
    done: bool = True
    total_duration: Optional[int] = None
    eval_count: Optional[int] = None


class GenerateResponse(BaseModel):
    """Non-streaming text generation response."""
    response: str
    model: str
    provider: str
    done: bool = True


class EmbedResponse(BaseModel):
    """Embedding response."""
    embeddings: list[list[float]]
    model: str
    dimensions: int


class ModelInfo(BaseModel):
    """Information about a registered model."""
    name: str
    provider: str
    display_name: str
    context_window: int
    capabilities: list[str]
    ram_estimate_gb: float
    description: str


class ProviderHealth(BaseModel):
    """Provider health status."""
    provider: str
    healthy: bool
    base_url: str


# ──────────────────────────────────────────────────────────────────────
#  Endpoints
# ──────────────────────────────────────────────────────────────────────


@router.post(
    "/chat",
    summary="Chat completion",
    description="Send messages to an LLM for a chat completion.  "
    "Set ``stream=true`` to receive tokens as Server-Sent Events.",
)
async def chat_completion(
    body: ChatRequest,
    request: Request,
    user: UserIdentity = Depends(require_permission(Permission.QUERY_LLM)),
):
    """
    Chat completion endpoint supporting both Ollama and LM Studio.

    When ``stream=true``, returns an SSE stream.
    When ``stream=false``, returns a JSON response.
    """
    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    if body.provider == "lmstudio":
        client = get_lmstudio_client()

        if body.stream:
            token_stream = client.chat_stream(
                messages=messages,
                model=body.model,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                system_prompt=body.system_prompt,
            )
            return stream_sse_response(token_stream, request, provider="lmstudio")

        result = await client.chat(
            messages=messages,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            system_prompt=body.system_prompt,
        )
        choices = result.get("choices", [])
        content = choices[0]["message"]["content"] if choices else ""
        return ChatResponse(
            content=content,
            model=result.get("model", body.model or "lmstudio"),
            provider="lmstudio",
        )

    # Default: Ollama
    client = get_ollama_client()

    if body.stream:
        token_stream = client.chat_stream(
            messages=messages,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            system_prompt=body.system_prompt,
        )
        return stream_sse_response(token_stream, request, provider="ollama")

    result = await client.chat(
        messages=messages,
        model=body.model,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        system_prompt=body.system_prompt,
    )
    msg = result.get("message", {})
    return ChatResponse(
        content=msg.get("content", ""),
        model=result.get("model", body.model or ""),
        provider="ollama",
        total_duration=result.get("total_duration"),
        eval_count=result.get("eval_count"),
    )


@router.post(
    "/generate",
    summary="Text generation",
    description="Raw text generation (prompt-in → text-out).",
)
async def generate_text(
    body: GenerateRequest,
    request: Request,
    user: UserIdentity = Depends(require_permission(Permission.QUERY_LLM)),
):
    """
    Raw text generation.  Supports streaming via SSE.
    """
    if body.provider == "lmstudio":
        client = get_lmstudio_client()

        if body.stream:
            # LM Studio doesn't have a /completions stream natively;
            # wrap into chat format
            messages = [{"role": "user", "content": body.prompt}]
            token_stream = client.chat_stream(
                messages=messages,
                model=body.model,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                system_prompt=body.system_prompt,
            )
            return stream_sse_response(token_stream, request, provider="lmstudio")

        result = await client.complete(
            prompt=body.prompt,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
        choices = result.get("choices", [])
        text = choices[0].get("text", "") if choices else ""
        return GenerateResponse(
            response=text,
            model=result.get("model", body.model or "lmstudio"),
            provider="lmstudio",
        )

    # Default: Ollama
    ollama = get_ollama_client()

    if body.stream:
        token_stream = ollama.generate_stream(
            prompt=body.prompt,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            system_prompt=body.system_prompt,
        )
        return stream_sse_response(token_stream, request, provider="ollama")

    result = await ollama.generate(
        prompt=body.prompt,
        model=body.model,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        system_prompt=body.system_prompt,
    )
    return GenerateResponse(
        response=result.get("response", ""),
        model=result.get("model", body.model or ""),
        provider="ollama",
    )


@router.post(
    "/embed",
    response_model=EmbedResponse,
    summary="Generate embeddings",
    description="Generate embeddings via Ollama's ``/api/embed`` endpoint.",
)
async def generate_embeddings(
    body: EmbedRequest,
    user: UserIdentity = Depends(require_permission(Permission.QUERY_LLM)),
) -> EmbedResponse:
    """Generate text embeddings using Ollama."""
    ollama = get_ollama_client()

    try:
        embeddings = await ollama.embed(
            input_text=body.input,
            model=body.model,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding generation failed: {exc}",
        ) from exc

    dimensions = len(embeddings[0]) if embeddings else 0

    return EmbedResponse(
        embeddings=embeddings,
        model=body.model or get_ollama_client()._settings.ollama_embed_model,
        dimensions=dimensions,
    )


@router.get(
    "/models",
    response_model=list[ModelInfo],
    summary="List registered models",
)
async def list_registered_models(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    user: UserIdentity = Depends(get_current_user),
) -> list[ModelInfo]:
    """List all models in the static registry, optionally filtered by provider."""
    prov = ModelProvider(provider) if provider else None
    models = list_models(prov)
    return [
        ModelInfo(
            name=m.name,
            provider=m.provider.value,
            display_name=m.display_name,
            context_window=m.context_window,
            capabilities=[c.value for c in m.capabilities],
            ram_estimate_gb=m.ram_estimate_gb,
            description=m.description,
        )
        for m in models
    ]


@router.get(
    "/models/available",
    summary="List models actually available in Ollama",
)
async def list_available_models(
    user: UserIdentity = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Query Ollama for currently downloaded models."""
    ollama = get_ollama_client()
    try:
        return await ollama.list_models()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to contact Ollama: {exc}",
        ) from exc


@router.post(
    "/models/pull",
    summary="Pull a model from Ollama registry",
    dependencies=[Depends(require_permission(Permission.MANAGE_MODELS))],
)
async def pull_model(
    model: str = Query(..., description="Model name to pull"),
    request: Request = None,
):
    """
    Pull a model from the Ollama registry.  Streams progress as SSE.
    """
    ollama = get_ollama_client()

    async def _progress_stream():
        try:
            async for event in ollama.pull_model(model):
                if request and await request.is_disconnected():
                    break
                yield f"data: {__import__('json').dumps(event)}\n\n"
        except Exception as exc:
            yield f"data: {__import__('json').dumps({'error': str(exc)})}\n\n"
        yield "data: [DONE]\n\n"

    from starlette.responses import StreamingResponse
    return StreamingResponse(
        content=_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete(
    "/models/{model_name}",
    summary="Delete a model from Ollama",
    dependencies=[Depends(require_permission(Permission.MANAGE_MODELS))],
)
async def delete_model(model_name: str) -> dict[str, Any]:
    """Delete a locally cached Ollama model."""
    ollama = get_ollama_client()
    success = await ollama.delete_model(model_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found or deletion failed",
        )
    return {"deleted": model_name, "success": True}


@router.get(
    "/health",
    response_model=list[ProviderHealth],
    summary="Check LLM provider health",
)
async def health_check() -> list[ProviderHealth]:
    """Check connectivity to all configured LLM providers."""
    from config.settings import get_settings
    settings = get_settings()

    ollama = get_ollama_client()
    lmstudio = get_lmstudio_client()

    ollama_ok = await ollama.health_check()
    lmstudio_ok = await lmstudio.health_check()

    return [
        ProviderHealth(
            provider="ollama",
            healthy=ollama_ok,
            base_url=settings.ollama_base_url,
        ),
        ProviderHealth(
            provider="lmstudio",
            healthy=lmstudio_ok,
            base_url=settings.lmstudio_base_url,
        ),
    ]
