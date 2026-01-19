"""
Integration tests for the full RAG pipeline.
"""

from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, Mock


class IntegrationTests(TestCase):
    """Integration tests."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    @patch('wagtail_context_search.views.RAGRetrieval')
    @patch('wagtail_context_search.views.RAGGenerator')
    def test_query_endpoint(self, mock_generator, mock_retrieval):
        """Test query API endpoint."""
        # Mock retrieval
        mock_retrieval_instance = Mock()
        mock_retrieval_instance.retrieve.return_value = [
            {
                "id": "test_1",
                "text": "Test content",
                "metadata": {"title": "Test Page", "url": "/test/"},
                "score": 0.9,
            }
        ]
        mock_retrieval.return_value = mock_retrieval_instance

        # Mock generator
        mock_generator_instance = Mock()
        mock_generator_instance.generate_answer.return_value = {
            "answer": "Test answer",
            "sources": [{"title": "Test Page", "url": "/test/", "score": 0.9}],
        }
        mock_generator.return_value = mock_generator_instance

        # Make request
        response = self.client.post(
            reverse('wagtail_context_search:query'),
            data={"query": "test question"},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('answer', data)
        self.assertIn('sources', data)

    def test_health_endpoint(self):
        """Test health check endpoint."""
        with patch('wagtail_context_search.views.RAGRetrieval') as mock_retrieval, \
             patch('wagtail_context_search.views.RAGGenerator') as mock_generator:
            
            # Mock backends as available
            mock_retrieval_instance = Mock()
            mock_retrieval_instance.embedder.is_available.return_value = True
            mock_retrieval_instance.vector_db.is_available.return_value = True
            mock_retrieval.return_value = mock_retrieval_instance

            mock_generator_instance = Mock()
            mock_generator_instance.llm.is_available.return_value = True
            mock_generator.return_value = mock_generator_instance

            response = self.client.get(reverse('wagtail_context_search:health'))
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('status', data)
