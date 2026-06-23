"""
Neel AI — Memory Router.

API endpoints for:
  - Semantic search (query memory)
  - Document ingestion (file upload & raw text)
  - Collection management
  - Memory statistics
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field

from auth.rbac import get_current_user, require_permission
from auth.schemas import UserIdentity
from config.governance import Permission
from config.settings import get_settings
from memory.chroma_client import get_chroma_client
from memory.embeddings import get_embedding_service
from memory.ingest import ingest_file, ingest_text

logger = logging.getLogger("neel.memory.router")

router = APIRouter(prefix="/api/v1/memory", tags=["Memory"])


# ──────────────────────────────────────────────────────────────────────
#  Schemas
# ──────────────────────────────────────────────────────────────────────


class MemoryQueryRequest(BaseModel):
    """Request body for semantic search."""
    query: str = Field(..., min_length=1, max_length=10000)
    collection: Optional[str] = None
    n_results: int = Field(5, ge=1, le=50)
    where: Optional[dict[str, Any]] = None


class MemoryQueryResult(BaseModel):
    """A single search result."""
    document: str
    metadata: dict[str, Any]
    distance: float
    id: str


class MemoryQueryResponse(BaseModel):
    """Response for a semantic search query."""
    query: str
    results: list[MemoryQueryResult]
    collection: str
    total_results: int


class TextIngestRequest(BaseModel):
    """Request body for ingesting raw text."""
    text: str = Field(..., min_length=1)
    source_name: str = "direct_input"
    collection: Optional[str] = None
    chunk_size: int = Field(500, ge=50, le=5000)
    chunk_overlap: int = Field(50, ge=0, le=500)
    metadata: Optional[dict[str, Any]] = None


class IngestResponse(BaseModel):
    """Response after successful ingestion."""
    source: str
    total_chunks: int
    total_characters: int
    document_ids: list[str]
    collection: str


class CollectionInfo(BaseModel):
    """Information about a ChromaDB collection."""
    name: str
    document_count: int


class MemoryStats(BaseModel):
    """Overall memory statistics."""
    collections: list[CollectionInfo]
    total_documents: int
    chromadb_healthy: bool


# ──────────────────────────────────────────────────────────────────────
#  Endpoints
# ──────────────────────────────────────────────────────────────────────


@router.post(
    "/query",
    response_model=MemoryQueryResponse,
    summary="Semantic search over memory",
)
async def query_memory(
    body: MemoryQueryRequest,
    user: UserIdentity = Depends(require_permission(Permission.QUERY_MEMORY)),
) -> MemoryQueryResponse:
    """
    Perform semantic search against the vector store.

    1. Embed the query text via Ollama /api/embed
    2. Search ChromaDB for nearest neighbours
    3. Return ranked results with documents, metadata, and distances
    """
    embedder = get_embedding_service()
    chroma = get_chroma_client()

    try:
        query_embedding = await embedder.embed_text(body.query)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to generate query embedding: {exc}",
        ) from exc

    try:
        raw_results = chroma.query(
            query_embedding=query_embedding,
            n_results=body.n_results,
            collection_name=body.collection,
            where=body.where,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"ChromaDB query failed: {exc}",
        ) from exc

    results: list[MemoryQueryResult] = []
    ids = raw_results.get("ids", [[]])[0]
    documents = raw_results.get("documents", [[]])[0]
    metadatas = raw_results.get("metadatas", [[]])[0]
    distances = raw_results.get("distances", [[]])[0]

    for i in range(len(ids)):
        results.append(
            MemoryQueryResult(
                id=ids[i],
                document=documents[i] if documents else "",
                metadata=metadatas[i] if metadatas else {},
                distance=distances[i] if distances else 0.0,
            )
        )

    settings = get_settings()
    collection = body.collection or settings.chroma_default_collection

    return MemoryQueryResponse(
        query=body.query,
        results=results,
        collection=collection,
        total_results=len(results),
    )


@router.post(
    "/ingest/text",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest raw text into memory",
)
async def ingest_text_endpoint(
    body: TextIngestRequest,
    user: UserIdentity = Depends(require_permission(Permission.INGEST_DOCUMENTS)),
) -> IngestResponse:
    """Chunk, embed, and store raw text in the vector store."""
    try:
        result = await ingest_text(
            text=body.text,
            source_name=body.source_name,
            collection_name=body.collection,
            chunk_size=body.chunk_size,
            chunk_overlap=body.chunk_overlap,
            extra_metadata=body.metadata,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ingestion failed: {exc}",
        ) from exc

    return IngestResponse(
        source=result["source"],
        total_chunks=result["total_chunks"],
        total_characters=result["total_characters"],
        document_ids=result["document_ids"],
        collection=result["collection"],
    )


@router.post(
    "/ingest/file",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a file into memory",
)
async def ingest_file_endpoint(
    file: UploadFile = File(...),
    collection: Optional[str] = Form(None),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(50),
    user: UserIdentity = Depends(require_permission(Permission.INGEST_DOCUMENTS)),
) -> IngestResponse:
    """
    Upload a file (PDF, TXT, MD), parse, chunk, embed, and store it.
    """
    settings = get_settings()

    # Validate file size
    if file.size and file.size > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds max size of {settings.max_upload_size_mb}MB",
        )

    # Save uploaded file
    upload_dir = settings.upload_path
    file_path = upload_dir / file.filename
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {exc}",
        ) from exc

    # Ingest
    try:
        result = await ingest_file(
            file_path=file_path,
            collection_name=collection,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            extra_metadata={"uploaded_by": user.email},
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ingestion failed: {exc}",
        ) from exc

    return IngestResponse(
        source=result["file"],
        total_chunks=result["total_chunks"],
        total_characters=result["total_characters"],
        document_ids=result["document_ids"],
        collection=result["collection"],
    )


@router.get(
    "/collections",
    response_model=list[CollectionInfo],
    summary="List all collections",
)
async def list_collections(
    user: UserIdentity = Depends(require_permission(Permission.QUERY_MEMORY)),
) -> list[CollectionInfo]:
    """List all ChromaDB collections with document counts."""
    chroma = get_chroma_client()
    names = chroma.list_collections()
    results = []
    for name in names:
        try:
            count = chroma.count(name)
        except Exception:
            count = 0
        results.append(CollectionInfo(name=name, document_count=count))
    return results


@router.delete(
    "/collections/{collection_name}",
    summary="Delete a collection",
    dependencies=[Depends(require_permission(Permission.MANAGE_MEMORY))],
)
async def delete_collection(collection_name: str) -> dict[str, Any]:
    """Delete an entire ChromaDB collection."""
    chroma = get_chroma_client()
    success = chroma.delete_collection(collection_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{collection_name}' not found",
        )
    return {"deleted": collection_name, "success": True}


@router.delete(
    "/documents",
    summary="Delete specific documents",
    dependencies=[Depends(require_permission(Permission.MANAGE_MEMORY))],
)
async def delete_documents(
    ids: list[str] = Query(..., description="Document IDs to delete"),
    collection: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Delete specific documents by their IDs."""
    chroma = get_chroma_client()
    success = chroma.delete_documents(ids, collection)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete documents",
        )
    return {"deleted_ids": ids, "success": True}


@router.get(
    "/stats",
    response_model=MemoryStats,
    summary="Memory statistics",
)
async def memory_stats(
    user: UserIdentity = Depends(get_current_user),
) -> MemoryStats:
    """Get overall memory statistics."""
    chroma = get_chroma_client()
    healthy = chroma.health_check()

    collections: list[CollectionInfo] = []
    total_docs = 0

    if healthy:
        names = chroma.list_collections()
        for name in names:
            try:
                count = chroma.count(name)
                total_docs += count
                collections.append(CollectionInfo(name=name, document_count=count))
            except Exception:
                collections.append(CollectionInfo(name=name, document_count=0))

    return MemoryStats(
        collections=collections,
        total_documents=total_docs,
        chromadb_healthy=healthy,
    )
