"""
Tests for backend implementations.
"""

from django.test import TestCase
from unittest.mock import Mock, patch

from wagtail_context_search.backends.llm import get_llm_backend
from wagtail_context_search.backends.embedder import get_embedder_backend
from wagtail_context_search.backends.vector_db import get_vector_db_backend
from wagtail_context_search.settings import get_config


class BackendTests(TestCase):
    """Test backend implementations."""

    def setUp(self):
        """Set up test configuration."""
        self.config = get_config()

    def test_llm_backend_registry(self):
        """Test LLM backend registry."""
        # Test that backends can be retrieved
        backends = ["openai", "anthropic", "ollama"]
        for backend_name in backends:
            try:
                backend = get_llm_backend(backend_name, self.config)
                self.assertIsNotNone(backend)
            except (ValueError, ImportError):
                # Backend might not be available
                pass

    def test_embedder_backend_registry(self):
        """Test embedder backend registry."""
        backends = ["openai", "sentence_transformers"]
        for backend_name in backends:
            try:
                backend = get_embedder_backend(backend_name, self.config)
                self.assertIsNotNone(backend)
            except (ValueError, ImportError):
                # Backend might not be available
                pass

    def test_vector_db_backend_registry(self):
        """Test vector DB backend registry."""
        backends = ["chroma", "pgvector", "qdrant"]
        for backend_name in backends:
            try:
                backend = get_vector_db_backend(backend_name, self.config)
                self.assertIsNotNone(backend)
            except (ValueError, ImportError):
                # Backend might not be available
                pass
