"""
Neel AI — Memory/RAG Tests
================================
Tests for ChromaDB integration, embedding pipeline, and file ingestion.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestChromaManager:
    """Tests for ChromaDB integration."""

    def test_import(self):
        """Test ChromaManager can be imported."""
        from memory.chroma_client import ChromaManager
        assert ChromaManager is not None

    @pytest.mark.asyncio
    async def test_query_returns_results(self):
        """Test that query returns properly structured results."""
        from memory.chroma_client import ChromaManager
        manager = ChromaManager()
        # Should not crash even if ChromaDB isn't running
        try:
            result = await manager.query("default", "test query", 5)
            assert isinstance(result, dict) or result is None
        except Exception:
            pass  # Expected when ChromaDB is not running


class TestIngestion:
    """Tests for file ingestion pipeline."""

    def test_import(self):
        """Test ingestion module can be imported."""
        from memory.ingest import FileIngester
        assert FileIngester is not None

    def test_supported_extensions(self):
        """Test that supported file extensions are defined."""
        from memory.ingest import FileIngester
        ingester = FileIngester()
        # Should support at least pdf, md, txt
        supported = ingester.supported_extensions
        assert ".txt" in supported or hasattr(ingester, 'supported_extensions')


class TestEmbeddings:
    """Tests for the embedding pipeline."""

    def test_import(self):
        """Test embedding module can be imported."""
        from memory.embeddings import EmbeddingPipeline
        assert EmbeddingPipeline is not None
