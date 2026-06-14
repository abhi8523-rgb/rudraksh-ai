"""
Rudraksh AI — SSE Streaming Utilities.

Provides helpers that convert async token iterators from Ollama / LM Studio
into FastAPI ``StreamingResponse`` objects using Server-Sent Events (SSE).

Headers set on every SSE response:
  - Cache-Control: no-cache
  - X-Accel-Buffering: no       (prevents nginx / reverse-proxy buffering)
  - Content-Type: text/event-stream
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Literal

from fastapi import Request
from starlette.responses import StreamingResponse

logger = logging.getLogger("rudraksh.llm.streaming")


async def _ollama_chat_event_generator(
    token_stream: AsyncIterator[dict[str, Any]],
    request: Request,
) -> AsyncIterator[str]:
    """
    Consume an Ollama chat stream and yield SSE-formatted events.

    Each event is a JSON string containing the incremental token.
    Disconnection is checked on every iteration via ``request.is_disconnected()``.
    """
    try:
        async for chunk in token_stream:
            if await request.is_disconnected():
                logger.info("Client disconnected — stopping Ollama stream")
                break

            content = ""
            if "message" in chunk:
                content = chunk["message"].get("content", "")
            elif "response" in chunk:
                content = chunk.get("response", "")

            done = chunk.get("done", False)

            event_data = {
                "content": content,
                "done": done,
            }

            # Include usage stats on the final chunk
            if done:
                event_data["total_duration"] = chunk.get("total_duration")
                event_data["eval_count"] = chunk.get("eval_count")
                event_data["eval_duration"] = chunk.get("eval_duration")

            yield f"data: {json.dumps(event_data)}\n\n"

            if done:
                break
    except Exception as exc:
        logger.error("Ollama stream error: %s", exc)
        error_event = {"error": str(exc), "done": True}
        yield f"data: {json.dumps(error_event)}\n\n"
    finally:
        yield "data: [DONE]\n\n"


async def _lmstudio_chat_event_generator(
    token_stream: AsyncIterator[dict[str, Any]],
    request: Request,
) -> AsyncIterator[str]:
    """
    Consume an LM Studio (OpenAI-format) stream and yield SSE events.
    """
    try:
        async for chunk in token_stream:
            if await request.is_disconnected():
                logger.info("Client disconnected — stopping LM Studio stream")
                break

            choices = chunk.get("choices", [])
            content = ""
            finish_reason = None
            if choices:
                delta = choices[0].get("delta", {})
                content = delta.get("content", "")
                finish_reason = choices[0].get("finish_reason")

            event_data = {
                "content": content,
                "done": finish_reason is not None,
            }

            if finish_reason:
                event_data["finish_reason"] = finish_reason
                usage = chunk.get("usage")
                if usage:
                    event_data["usage"] = usage

            yield f"data: {json.dumps(event_data)}\n\n"

            if finish_reason:
                break
    except Exception as exc:
        logger.error("LM Studio stream error: %s", exc)
        error_event = {"error": str(exc), "done": True}
        yield f"data: {json.dumps(error_event)}\n\n"
    finally:
        yield "data: [DONE]\n\n"


def stream_sse_response(
    token_stream: AsyncIterator[dict[str, Any]],
    request: Request,
    provider: Literal["ollama", "lmstudio"] = "ollama",
) -> StreamingResponse:
    """
    Build a ``StreamingResponse`` that streams LLM tokens as SSE events.

    Sets the required headers:
      - ``Cache-Control: no-cache``
      - ``X-Accel-Buffering: no``

    Args:
        token_stream: Async iterator of token dicts from Ollama or LM Studio.
        request: The incoming FastAPI Request (used for disconnect detection).
        provider: Which provider format the stream is in.

    Returns:
        A configured ``StreamingResponse`` with SSE content type.
    """
    if provider == "lmstudio":
        generator = _lmstudio_chat_event_generator(token_stream, request)
    else:
        generator = _ollama_chat_event_generator(token_stream, request)

    return StreamingResponse(
        content=generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def create_sse_stream(
    token_iterator: AsyncIterator[dict[str, Any]],
) -> StreamingResponse:
    """
    Build an SSE ``StreamingResponse`` from an async token iterator.

    Simplified version for module routers that don't have access to
    the FastAPI ``Request`` object. Does not check for client disconnect.

    Each Ollama chunk is expected to have ``message.content`` or ``response``.
    """

    async def _generate() -> AsyncIterator[str]:
        try:
            async for chunk in token_iterator:
                content = ""
                if "message" in chunk:
                    content = chunk["message"].get("content", "")
                elif "response" in chunk:
                    content = chunk.get("response", "")

                done = chunk.get("done", False)

                event_data = {"content": content, "done": done}

                if done:
                    event_data["eval_count"] = chunk.get("eval_count")
                    event_data["total_duration"] = chunk.get("total_duration")

                yield f"data: {json.dumps(event_data)}\n\n"

                if done:
                    break
        except Exception as exc:
            logger.error("Stream error: %s", exc)
            yield f"data: {json.dumps({'error': str(exc), 'done': True})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        content=_generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
