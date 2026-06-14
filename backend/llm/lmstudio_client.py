"""
Rudraksh AI — LM Studio Async Client.

Communicates with LM Studio via its OpenAI-compatible REST API
(default: ``http://localhost:1234/v1``).

LM Studio exposes standard ``/v1/chat/completions``, ``/v1/completions``,
and ``/v1/models`` endpoints.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx

from config.settings import Settings, get_settings

logger = logging.getLogger("rudraksh.llm.lmstudio")


class LMStudioClient:
    """
    Async HTTP client for LM Studio's OpenAI-compatible API.

    In Docker the base URL should be ``http://host.docker.internal:1234/v1``.
    For local dev it defaults to ``http://localhost:1234/v1``.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._base_url = self._settings.lmstudio_base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    # ── Lifecycle ────────────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._settings.lmstudio_timeout),
                limits=httpx.Limits(
                    max_connections=5,
                    max_keepalive_connections=3,
                ),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ── Health ───────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        """Return True if LM Studio is reachable."""
        try:
            client = await self._get_client()
            resp = await client.get("/models", timeout=5.0)
            return resp.status_code == 200
        except (httpx.HTTPError, httpx.ConnectError):
            return False

    # ── Models ───────────────────────────────────────────────────────

    async def list_models(self) -> list[dict[str, Any]]:
        """List models currently loaded in LM Studio."""
        client = await self._get_client()
        resp = await client.get("/models")
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])

    # ── Chat Completion (non-streaming) ──────────────────────────────

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a chat completion request (non-streaming).

        LM Studio uses the OpenAI-compatible ``/v1/chat/completions`` format.
        """
        model = model or self._settings.lmstudio_default_model
        max_tokens = max_tokens or self._settings.ollama_max_tokens

        msgs = list(messages)
        if system_prompt:
            msgs = [{"role": "system", "content": system_prompt}, *msgs]

        payload: dict[str, Any] = {
            "model": model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        client = await self._get_client()
        resp = await client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        return resp.json()

    # ── Chat Completion (streaming) ──────────────────────────────────

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream chat completion tokens from LM Studio.

        Yields OpenAI-format chunks with ``choices[0].delta.content``.
        """
        model = model or self._settings.lmstudio_default_model
        max_tokens = max_tokens or self._settings.ollama_max_tokens

        msgs = list(messages)
        if system_prompt:
            msgs = [{"role": "system", "content": system_prompt}, *msgs]

        payload: dict[str, Any] = {
            "model": model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        client = await self._get_client()
        async with client.stream(
            "POST", "/chat/completions", json=payload
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                line = line.strip()
                if not line or line == "data: [DONE]":
                    continue
                if line.startswith("data: "):
                    line = line[6:]
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse LM Studio stream chunk: %s", line)

    # ── Text Completion (non-streaming) ──────────────────────────────

    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Raw text completion (non-streaming)."""
        model = model or self._settings.lmstudio_default_model
        max_tokens = max_tokens or self._settings.ollama_max_tokens

        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        client = await self._get_client()
        resp = await client.post("/completions", json=payload)
        resp.raise_for_status()
        return resp.json()


# ──────────────────────────────────────────────────────────────────────
#  Module-level singleton accessor
# ──────────────────────────────────────────────────────────────────────

_lmstudio_client: LMStudioClient | None = None


def get_lmstudio_client() -> LMStudioClient:
    """Return (or create) the module-level LM Studio client singleton."""
    global _lmstudio_client
    if _lmstudio_client is None:
        _lmstudio_client = LMStudioClient()
    return _lmstudio_client
