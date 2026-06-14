"""
Rudraksh AI — ChromaDB Client.

Manages connections to ChromaDB in ``HttpClient`` mode and provides
high-level operations for collection management, document storage,
and semantic search.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import Settings, get_settings

logger = logging.getLogger("rudraksh.memory.chroma")


class ChromaMemoryClient:
    """
    High-level wrapper around ChromaDB's HttpClient.

    Handles collection lifecycle, document upsert, and similarity search.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: chromadb.HttpClient | None = None

    # ── Lifecycle ────────────────────────────────────────────────────

    def _get_client(self) -> chromadb.HttpClient:
        """Lazy-initialise the ChromaDB HTTP client."""
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=self._settings.chroma_host,
                port=self._settings.chroma_port,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                ),
            )
            logger.info(
                "Connected to ChromaDB at %s:%d",
                self._settings.chroma_host,
                self._settings.chroma_port,
            )
        return self._client

    def health_check(self) -> bool:
        """Return True if ChromaDB is reachable."""
        try:
            client = self._get_client()
            client.heartbeat()
            return True
        except Exception:
            return False

    # ── Collections ──────────────────────────────────────────────────

    def list_collections(self) -> list[str]:
        """Return names of all existing collections."""
        client = self._get_client()
        collections = client.list_collections()
        return [c.name for c in collections]

    def get_or_create_collection(
        self,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> chromadb.Collection:
        """
        Get an existing collection or create one.

        Defaults to the configured default collection name.
        """
        name = name or self._settings.chroma_default_collection
        client = self._get_client()
        return client.get_or_create_collection(
            name=name,
            metadata=metadata or {"hnsw:space": "cosine"},
        )

    def delete_collection(self, name: str) -> bool:
        """Delete a collection by name."""
        try:
            client = self._get_client()
            client.delete_collection(name=name)
            logger.info("Deleted collection: %s", name)
            return True
        except Exception as exc:
            logger.error("Failed to delete collection %s: %s", name, exc)
            return False

    # ── Documents ────────────────────────────────────────────────────

    def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
        collection_name: str | None = None,
    ) -> list[str]:
        """
        Add documents with pre-computed embeddings to a collection.

        Args:
            documents: The raw text chunks.
            embeddings: Corresponding embedding vectors.
            metadatas: Optional metadata dicts (one per document).
            ids: Optional document IDs.  Generated if not provided.
            collection_name: Target collection.

        Returns:
            List of document IDs that were inserted.
        """
        collection = self.get_or_create_collection(collection_name)

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        if metadatas is None:
            metadatas = [{}] * len(documents)

        # Ensure metadata values are primitives (ChromaDB requirement)
        clean_meta = []
        for m in metadatas:
            clean = {}
            for k, v in m.items():
                if isinstance(v, (str, int, float, bool)):
                    clean[k] = v
                else:
                    clean[k] = str(v)
            clean_meta.append(clean)

        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=clean_meta,
            ids=ids,
        )

        logger.info(
            "Added %d documents to collection '%s'",
            len(documents),
            collection.name,
        )
        return ids

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        collection_name: str | None = None,
        where: dict[str, Any] | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Query for similar documents using a pre-computed embedding.

        Args:
            query_embedding: The query vector.
            n_results: Number of results to return.
            collection_name: Collection to search.
            where: Optional metadata filter.
            include: What to include in results (documents, metadatas, distances).

        Returns:
            ChromaDB query result dict.
        """
        collection = self.get_or_create_collection(collection_name)
        include = include or ["documents", "metadatas", "distances"]

        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": include,
        }
        if where:
            kwargs["where"] = where

        return collection.query(**kwargs)

    def get_document(
        self,
        doc_id: str,
        collection_name: str | None = None,
    ) -> dict[str, Any] | None:
        """Retrieve a single document by ID."""
        collection = self.get_or_create_collection(collection_name)
        result = collection.get(ids=[doc_id], include=["documents", "metadatas"])
        if not result["ids"]:
            return None
        return {
            "id": result["ids"][0],
            "document": result["documents"][0] if result["documents"] else None,
            "metadata": result["metadatas"][0] if result["metadatas"] else None,
        }

    def delete_documents(
        self,
        ids: list[str],
        collection_name: str | None = None,
    ) -> bool:
        """Delete documents by ID from a collection."""
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(ids=ids)
            logger.info("Deleted %d documents", len(ids))
            return True
        except Exception as exc:
            logger.error("Failed to delete documents: %s", exc)
            return False

    def count(self, collection_name: str | None = None) -> int:
        """Return the number of documents in a collection."""
        collection = self.get_or_create_collection(collection_name)
        return collection.count()


# ──────────────────────────────────────────────────────────────────────
#  Singleton
# ──────────────────────────────────────────────────────────────────────

_chroma_client: ChromaMemoryClient | None = None


def get_chroma_client() -> ChromaMemoryClient:
    """Return the module-level ChromaDB client singleton."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaMemoryClient()
    return _chroma_client
