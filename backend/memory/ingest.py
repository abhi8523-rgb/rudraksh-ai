"""
Neel AI — Document Ingestion Pipeline.

Supports ingesting:
  - Plain text (.txt)
  - Markdown (.md)
  - PDF files (.pdf) via pypdf

Pipeline:
  1. Parse document into raw text
  2. Chunk text into overlapping segments
  3. Generate embeddings for each chunk
  4. Store chunks + embeddings in ChromaDB
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from memory.chroma_client import ChromaMemoryClient, get_chroma_client
from memory.embeddings import EmbeddingService, get_embedding_service

logger = logging.getLogger("neel.memory.ingest")


# ──────────────────────────────────────────────────────────────────────
#  Document Parsers
# ──────────────────────────────────────────────────────────────────────


def _parse_text_file(file_path: Path) -> str:
    """Read a plain text or markdown file."""
    return file_path.read_text(encoding="utf-8", errors="replace")


def _parse_pdf_file(file_path: Path) -> str:
    """Extract text from a PDF using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


_PARSERS: dict[str, callable] = {
    ".txt": _parse_text_file,
    ".md": _parse_text_file,
    ".markdown": _parse_text_file,
    ".pdf": _parse_pdf_file,
    ".text": _parse_text_file,
}


def parse_document(file_path: Path) -> str:
    """
    Parse a document into raw text.

    Raises ValueError if the file extension is not supported.
    """
    ext = file_path.suffix.lower()
    parser = _PARSERS.get(ext)
    if parser is None:
        raise ValueError(
            f"Unsupported file type: {ext}. "
            f"Supported: {', '.join(_PARSERS.keys())}"
        )
    return parser(file_path)


# ──────────────────────────────────────────────────────────────────────
#  Ingestion Pipeline
# ──────────────────────────────────────────────────────────────────────


async def ingest_file(
    file_path: Path,
    collection_name: str | None = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    extra_metadata: dict[str, Any] | None = None,
    chroma: ChromaMemoryClient | None = None,
    embedder: EmbeddingService | None = None,
) -> dict[str, Any]:
    """
    Ingest a single file into the vector store.

    Returns a summary dict with ingestion statistics.
    """
    chroma = chroma or get_chroma_client()
    embedder = embedder or get_embedding_service()

    # 1. Parse
    logger.info("Parsing document: %s", file_path.name)
    raw_text = parse_document(file_path)
    if not raw_text.strip():
        raise ValueError(f"Document is empty: {file_path.name}")

    # 2. Chunk
    chunks = EmbeddingService.chunk_text(
        raw_text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    logger.info("Split into %d chunks", len(chunks))

    if not chunks:
        raise ValueError("No chunks produced from document")

    # 3. Embed (batch)
    embeddings = await embedder.embed_batch(chunks)
    logger.info("Generated %d embeddings", len(embeddings))

    # 4. Build metadata
    file_hash = hashlib.sha256(raw_text.encode()).hexdigest()[:16]
    now_iso = datetime.now(timezone.utc).isoformat()

    metadatas = []
    for i, chunk in enumerate(chunks):
        meta = {
            "source": file_path.name,
            "source_path": str(file_path),
            "chunk_index": i,
            "total_chunks": len(chunks),
            "file_hash": file_hash,
            "ingested_at": now_iso,
            "char_count": len(chunk),
        }
        if extra_metadata:
            meta.update(extra_metadata)
        metadatas.append(meta)

    # 5. Store
    doc_ids = chroma.add_documents(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        collection_name=collection_name,
    )

    result = {
        "file": file_path.name,
        "total_chunks": len(chunks),
        "total_characters": len(raw_text),
        "document_ids": doc_ids,
        "collection": collection_name or chroma._settings.chroma_default_collection,
        "file_hash": file_hash,
        "ingested_at": now_iso,
    }
    logger.info("Ingestion complete: %s", result)
    return result


async def ingest_text(
    text: str,
    source_name: str = "direct_input",
    collection_name: str | None = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    extra_metadata: dict[str, Any] | None = None,
    chroma: ChromaMemoryClient | None = None,
    embedder: EmbeddingService | None = None,
) -> dict[str, Any]:
    """
    Ingest raw text directly (without a file) into the vector store.
    """
    chroma = chroma or get_chroma_client()
    embedder = embedder or get_embedding_service()

    if not text.strip():
        raise ValueError("Cannot ingest empty text")

    chunks = EmbeddingService.chunk_text(
        text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    embeddings = await embedder.embed_batch(chunks)

    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    now_iso = datetime.now(timezone.utc).isoformat()

    metadatas = []
    for i, chunk in enumerate(chunks):
        meta = {
            "source": source_name,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "text_hash": text_hash,
            "ingested_at": now_iso,
            "char_count": len(chunk),
        }
        if extra_metadata:
            meta.update(extra_metadata)
        metadatas.append(meta)

    doc_ids = chroma.add_documents(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        collection_name=collection_name,
    )

    return {
        "source": source_name,
        "total_chunks": len(chunks),
        "total_characters": len(text),
        "document_ids": doc_ids,
        "collection": collection_name or chroma._settings.chroma_default_collection,
        "text_hash": text_hash,
        "ingested_at": now_iso,
    }
