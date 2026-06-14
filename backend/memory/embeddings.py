"""
Rudraksh AI — Embedding Service.

Generates text embeddings using Ollama's ``/api/embed`` endpoint
(nomic-embed-text by default).  Provides chunking utilities for
long documents.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from llm.ollama_client import OllamaClient, get_ollama_client
from config.settings import Settings, get_settings

logger = logging.getLogger("rudraksh.memory.embeddings")


class EmbeddingService:
    """
    Embedding generation service backed by Ollama /api/embed.

    Provides:
      - Single and batch text embedding
      - Text chunking for long documents
      - Overlap-aware sliding window chunking
    """

    def __init__(
        self,
        ollama: OllamaClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._ollama = ollama or get_ollama_client()
        self._settings = settings or get_settings()
        self._model = self._settings.ollama_embed_model

    # ── Embedding ────────────────────────────────────────────────────

    async def embed_text(
        self,
        text: str,
        model: str | None = None,
    ) -> list[float]:
        """
        Generate an embedding vector for a single string.

        Uses Ollama ``/api/embed`` (NOT /api/embeddings).
        """
        model = model or self._model
        embeddings = await self._ollama.embed(input_text=text, model=model)
        if not embeddings:
            raise ValueError("No embedding returned from Ollama")
        return embeddings[0]

    async def embed_batch(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """
        Generate embeddings for a batch of strings.

        Ollama's ``/api/embed`` accepts a list of inputs natively.
        """
        if not texts:
            return []
        model = model or self._model
        return await self._ollama.embed(input_text=texts, model=model)

    # ── Text Chunking ────────────────────────────────────────────────

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separator: str = "\n\n",
    ) -> list[str]:
        """
        Split text into overlapping chunks.

        Strategy:
          1. Split on the given separator (paragraph breaks by default).
          2. Accumulate paragraphs until ``chunk_size`` characters is reached.
          3. Overlap by keeping the last ``chunk_overlap`` characters of the
             previous chunk at the start of the next.

        Args:
            text: The full text to chunk.
            chunk_size: Maximum characters per chunk.
            chunk_overlap: Number of overlapping characters between consecutive chunks.
            separator: Primary split separator.

        Returns:
            List of text chunks.
        """
        if not text.strip():
            return []

        # Normalise whitespace
        text = re.sub(r"\r\n", "\n", text)

        # Split into paragraphs
        paragraphs = text.split(separator)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks: list[str] = []
        current_chunk: list[str] = []
        current_length = 0

        for para in paragraphs:
            para_len = len(para)

            if current_length + para_len + 1 > chunk_size and current_chunk:
                # Flush current chunk
                chunk_text = separator.join(current_chunk)
                chunks.append(chunk_text)

                # Determine overlap: take trailing paragraphs that fit in overlap
                overlap_text = ""
                overlap_parts: list[str] = []
                for prev in reversed(current_chunk):
                    if len(overlap_text) + len(prev) + 1 <= chunk_overlap:
                        overlap_parts.insert(0, prev)
                        overlap_text = separator.join(overlap_parts)
                    else:
                        break

                current_chunk = overlap_parts
                current_length = len(overlap_text)

            current_chunk.append(para)
            current_length += para_len + len(separator)

        # Flush remaining
        if current_chunk:
            chunks.append(separator.join(current_chunk))

        # Handle single-paragraph documents that exceed chunk_size
        final_chunks: list[str] = []
        for chunk in chunks:
            if len(chunk) > chunk_size * 1.5:
                # Force split by sentences
                sentences = re.split(r"(?<=[.!?])\s+", chunk)
                sub_chunk: list[str] = []
                sub_len = 0
                for sent in sentences:
                    if sub_len + len(sent) > chunk_size and sub_chunk:
                        final_chunks.append(" ".join(sub_chunk))
                        sub_chunk = []
                        sub_len = 0
                    sub_chunk.append(sent)
                    sub_len += len(sent) + 1
                if sub_chunk:
                    final_chunks.append(" ".join(sub_chunk))
            else:
                final_chunks.append(chunk)

        return final_chunks


# ──────────────────────────────────────────────────────────────────────
#  Singleton
# ──────────────────────────────────────────────────────────────────────

_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Return the module-level embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
