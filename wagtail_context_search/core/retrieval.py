"""
RAG retrieval pipeline for finding relevant documents.
"""

from typing import Any, Dict, List

from wagtail_context_search.backends.embedder import get_embedder_backend
from wagtail_context_search.backends.vector_db import get_vector_db_backend
from wagtail_context_search.settings import get_config


class RAGRetrieval:
    """Handles retrieval of relevant documents for RAG."""

    def __init__(self, config: Dict = None):
        """
        Initialize retrieval system.

        Args:
            config: Configuration dict (uses default if None)
        """
        self.config = config or get_config()
        self.embedder = get_embedder_backend(
            self.config.get("EMBEDDER_BACKEND", "openai"),
            self.config,
        )
        self.vector_db = get_vector_db_backend(
            self.config.get("VECTOR_DB_BACKEND", "chroma"),
            self.config,
        )
        self.top_k = self.config.get("TOP_K", 5)

    def retrieve(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: User query string
            top_k: Number of documents to retrieve (uses config default if None)

        Returns:
            List of document dicts with 'id', 'text', 'metadata', 'score'
        """
        if top_k is None:
            top_k = self.top_k

        # Generate query embedding
        query_embedding = self.embedder.embed(query)

        # Search vector database
        documents = self.vector_db.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )

        return documents

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the vector database.

        Args:
            documents: List of document dicts with 'id', 'text', 'metadata'
        """
        if not documents:
            return

        # Generate embeddings
        texts = [doc["text"] for doc in documents]
        embeddings = self.embedder.embed_batch(texts)

        # Add to vector DB
        self.vector_db.add_documents(documents, embeddings)

    def delete_documents(self, document_ids: List[str]) -> None:
        """
        Delete documents from the vector database.

        Args:
            document_ids: List of document IDs to delete
        """
        self.vector_db.delete_documents(document_ids)
