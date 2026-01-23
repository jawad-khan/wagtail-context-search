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

        # For Meilisearch, we should use vector search (embeddings) for semantic similarity
        # Text search in Meilisearch is for full-text search, not semantic similarity
        # Only use text search if vector search is not available
        use_vector_search = True
        
        # Check if this is Meilisearch - if so, use vector search instead of text search
        if hasattr(self.vector_db, "search_text") and hasattr(self.vector_db, "__class__"):
            # For Meilisearch, prefer vector search for semantic similarity
            # Text search can be used as a fallback or hybrid approach
            backend_name = self.vector_db.__class__.__name__.lower()
            if "meilisearch" in backend_name:
                use_vector_search = True  # Use vector search for Meilisearch
            else:
                # For other backends that support text search, use it
                use_vector_search = False
        
        if use_vector_search:
            # Generate query embedding
            query_embedding = self.embedder.embed(query)

            # Search vector database using embeddings
            documents = self.vector_db.search(
                query_embedding=query_embedding,
                top_k=top_k,
            )
        elif hasattr(self.vector_db, "search_text"):
            # Fallback to text search if vector search not available
            documents = self.vector_db.search_text(query, top_k=top_k)
        else:
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

        try:
            # Generate embeddings
            texts = [doc["text"] for doc in documents]
            
            if not texts:
                raise ValueError("No texts to embed")
            
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Generating embeddings for {len(texts)} documents")
            
            embeddings = self.embedder.embed_batch(texts)
            
            if not embeddings:
                raise ValueError("No embeddings generated")
            
            if len(embeddings) != len(documents):
                raise ValueError(f"Embedding count ({len(embeddings)}) doesn't match document count ({len(documents)})")
            
            logger.debug(f"Generated {len(embeddings)} embeddings, dimension: {len(embeddings[0]) if embeddings else 0}")

            # Add to vector DB
            logger.debug(f"Adding {len(documents)} documents to vector DB")
            self.vector_db.add_documents(documents, embeddings)
            logger.debug("Successfully added documents to vector DB")
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to add documents to vector DB: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def delete_documents(self, document_ids: List[str]) -> None:
        """
        Delete documents from the vector database.

        Args:
            document_ids: List of document IDs to delete
        """
        self.vector_db.delete_documents(document_ids)
