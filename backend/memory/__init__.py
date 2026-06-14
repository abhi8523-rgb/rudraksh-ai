"""
Rudraksh AI — Memory Package.

Provides ChromaDB-backed vector memory for RAG:
  - ChromaDB client (HttpClient mode)
  - Embedding generation via Ollama /api/embed
  - Document ingestion (PDF, text, markdown)
  - Memory query router
"""

from memory.chroma_client import ChromaMemoryClient, get_chroma_client
from memory.embeddings import EmbeddingService, get_embedding_service

__all__ = [
    "ChromaMemoryClient",
    "get_chroma_client",
    "EmbeddingService",
    "get_embedding_service",
]
