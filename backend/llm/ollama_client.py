"""
Rudraksh AI — Ollama Async Client.

Wraps the Ollama REST API with ``httpx.AsyncClient`` for:
  - Chat completions (streaming & non-streaming)
  - Text generation
  - Embeddings via ``/api/embed`` (NOT /api/embeddings)
  - Model management (list, pull, delete)
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx

from config.settings import Settings, get_settings

logger = logging.getLogger("rudraksh.llm.ollama")


class OllamaClient:
    """
    Async HTTP client for the Ollama API.

    The client is designed to be instantiated once and reused across
    the application lifetime.  It manages its own ``httpx.AsyncClient``
    connection pool.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._base_url = self._settings.ollama_base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    # ── Lifecycle ────────────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-initialise the httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._settings.ollama_timeout),
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5,
                ),
            )
        return self._client

    async def close(self) -> None:
        """Gracefully close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ── Health ───────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        """Return True if Ollama is reachable."""
        try:
            client = await self._get_client()
            resp = await client.get("/", timeout=5.0)
            return resp.status_code == 200
        except (httpx.HTTPError, httpx.ConnectError):
            return False

    # ── Models ───────────────────────────────────────────────────────

    async def list_models(self) -> list[dict[str, Any]]:
        """List all locally available models."""
        client = await self._get_client()
        resp = await client.get("/api/tags")
        resp.raise_for_status()
        data = resp.json()
        return data.get("models", [])

    async def pull_model(self, model: str) -> AsyncIterator[dict[str, Any]]:
        """Pull a model from the registry.  Yields progress events."""
        client = await self._get_client()
        async with client.stream(
            "POST",
            "/api/pull",
            json={"name": model},
            timeout=httpx.Timeout(600.0),
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.strip():
                    yield json.loads(line)

    async def delete_model(self, model: str) -> bool:
        """Delete a locally cached model."""
        client = await self._get_client()
        resp = await client.delete("/api/delete", json={"name": model})
        return resp.status_code == 200

    async def show_model(self, model: str) -> dict[str, Any]:
        """Get detailed information about a model."""
        client = await self._get_client()
        resp = await client.post("/api/show", json={"name": model})
        resp.raise_for_status()
        return resp.json()

    # ── Chat (non-streaming) ─────────────────────────────────────────

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a chat completion request to Ollama (non-streaming).

        Returns the full response dict including ``message.content``.
        """
        model = model or self._settings.ollama_default_model
        max_tokens = max_tokens or self._settings.ollama_max_tokens

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system_prompt:
            payload["messages"] = [
                {"role": "system", "content": system_prompt},
                *messages,
            ]

        client = await self._get_client()
        resp = await client.post("/api/chat", json=payload)
        resp.raise_for_status()
        return resp.json()

    # ── Chat (streaming) ─────────────────────────────────────────────

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream chat completion tokens from Ollama.

        Yields incremental response dicts.  Each dict contains
        ``message.content`` with the next token(s).
        """
        model = model or self._settings.ollama_default_model
        max_tokens = max_tokens or self._settings.ollama_max_tokens

        msgs = list(messages)
        if system_prompt:
            msgs = [{"role": "system", "content": system_prompt}, *msgs]

        payload: dict[str, Any] = {
            "model": model,
            "messages": msgs,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        client = await self._get_client()
        async with client.stream(
            "POST", "/api/chat", json=payload
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.strip():
                    yield json.loads(line)

    # ── Generate (non-streaming) ─────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Raw text generation (non-streaming).
        """
        model = model or self._settings.ollama_default_model
        max_tokens = max_tokens or self._settings.ollama_max_tokens

        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        client = await self._get_client()
        resp = await client.post("/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()

    # ── Generate (streaming) ─────────────────────────────────────────

    async def generate_stream(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream raw text generation tokens."""
        model = model or self._settings.ollama_default_model
        max_tokens = max_tokens or self._settings.ollama_max_tokens

        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        client = await self._get_client()
        async with client.stream(
            "POST", "/api/generate", json=payload
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.strip():
                    yield json.loads(line)

    # ── Embeddings (endpoint: /api/embed) ────────────────────────────

    async def embed(
        self,
        input_text: str | list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """
        Generate embeddings using Ollama's ``/api/embed`` endpoint.

        **Important**: The correct endpoint is ``/api/embed``, NOT
        ``/api/embeddings``.

        Args:
            input_text: A single string or list of strings to embed.
            model: Embedding model name (defaults to nomic-embed-text).

        Returns:
            A list of embedding vectors (one per input string).
        """
        model = model or self._settings.ollama_embed_model

        # Ollama /api/embed accepts "input" as string or list
        payload: dict[str, Any] = {
            "model": model,
            "input": input_text,
        }

        client = await self._get_client()
        resp = await client.post("/api/embed", json=payload)
        resp.raise_for_status()
        data = resp.json()

        # Ollama returns {"embeddings": [[...], [...]]}
        embeddings = data.get("embeddings", [])
        return embeddings


# ──────────────────────────────────────────────────────────────────────
#  Module-level singleton accessor
# ──────────────────────────────────────────────────────────────────────

_ollama_client: OllamaClient | None = None


def get_ollama_client() -> OllamaClient:
    """Return (or create) the module-level Ollama client singleton."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
