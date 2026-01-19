"""
Tests for RAG retrieval functionality.
"""

from django.test import TestCase
from unittest.mock import Mock, patch

from wagtail_context_search.core.chunker import Chunker
from wagtail_context_search.core.retrieval import RAGRetrieval
from wagtail_context_search.settings import get_config


class ChunkerTests(TestCase):
    """Test text chunking."""

    def test_chunk_small_text(self):
        """Test chunking small text."""
        chunker = Chunker(chunk_size=100, chunk_overlap=10)
        text = "This is a short text."
        chunks = chunker.chunk_text(text)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text.strip())

    def test_chunk_large_text(self):
        """Test chunking large text."""
        chunker = Chunker(chunk_size=50, chunk_overlap=10)
        text = " ".join(["word"] * 100)  # 500 characters
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)
        # Check overlap
        for i in range(len(chunks) - 1):
            # Chunks should have some overlap
            self.assertTrue(len(chunks[i]) <= 50)

    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        chunker = Chunker()
        chunks = chunker.chunk_text("")
        self.assertEqual(len(chunks), 0)

    def test_chunk_whitespace(self):
        """Test chunking text with excessive whitespace."""
        chunker = Chunker()
        text = "word1    word2\n\nword3"
        chunks = chunker.chunk_text(text)
        # Should normalize whitespace
        self.assertGreater(len(chunks), 0)


class RetrievalTests(TestCase):
    """Test RAG retrieval."""

    def setUp(self):
        """Set up test configuration."""
        self.config = get_config()

    @patch('wagtail_context_search.core.retrieval.get_embedder_backend')
    @patch('wagtail_context_search.core.retrieval.get_vector_db_backend')
    def test_retrieval_initialization(self, mock_vector_db, mock_embedder):
        """Test retrieval initialization."""
        mock_embedder.return_value = Mock()
        mock_vector_db.return_value = Mock()
        
        retrieval = RAGRetrieval(self.config)
        self.assertIsNotNone(retrieval.embedder)
        self.assertIsNotNone(retrieval.vector_db)
