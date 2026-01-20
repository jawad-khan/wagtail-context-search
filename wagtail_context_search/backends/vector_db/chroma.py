"""
ChromaDB vector database backend implementation.
"""

from typing import Any, Dict, List, Optional

from wagtail_context_search.backends.vector_db.base import BaseVectorDB


class ChromaBackend(BaseVectorDB):
    """ChromaDB vector database backend."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize ChromaDB backend."""
        super().__init__(config)
        self.persist_directory = self.backend_settings.get("persist_directory")
        # If no persist directory (None or empty), use a default one in the project
        if not self.persist_directory:
            import os
            try:
                from django.conf import settings
                # Try to use a directory relative to the project
                base_dir = getattr(settings, 'BASE_DIR', None)
                if base_dir:
                    self.persist_directory = os.path.join(base_dir, 'chroma_db')
                else:
                    # Fallback to current directory
                    self.persist_directory = os.path.abspath('./chroma_db')
            except Exception:
                # If Django settings not available, use current directory
                self.persist_directory = os.path.abspath('./chroma_db')
        self._client = None
        self._collection = None

    def _get_client(self):
        """Lazy load ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                import os
                from chromadb.config import Settings

                if self.persist_directory:
                    # Ensure directory exists
                    os.makedirs(self.persist_directory, exist_ok=True)
                    self._client = chromadb.PersistentClient(
                        path=self.persist_directory
                    )
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"ChromaDB using persistent storage: {os.path.abspath(self.persist_directory)}")
                else:
                    self._client = chromadb.Client(Settings(anonymized_telemetry=False))
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning("ChromaDB using in-memory storage (data will be lost on restart)")
            except ImportError:
                raise ImportError(
                    "chromadb package is required. Install with: pip install chromadb"
                )
        return self._client

    def _get_collection(self, dimension: int):
        """Get or create collection."""
        client = self._get_client()
        try:
            # Try to get existing collection
            collection = client.get_collection(self.collection_name)
            # Check if dimension matches (if collection has documents)
            try:
                count = collection.count()
                if count > 0:
                    # Get a sample to check dimension
                    sample = collection.get(limit=1)
                    if sample.get("embeddings") and len(sample["embeddings"]) > 0:
                        existing_dim = len(sample["embeddings"][0])
                        if existing_dim != dimension:
                            raise ValueError(
                                f"Dimension mismatch: collection has {existing_dim}, trying to add {dimension}"
                            )
            except Exception:
                pass  # Collection might be empty, that's ok
            self._collection = collection
        except Exception:
            # Collection doesn't exist, create it
            self._collection = client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def is_available(self) -> bool:
        """Check if ChromaDB is available."""
        try:
            self._get_client()
            return True
        except Exception:
            return False

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> None:
        """Add documents to ChromaDB."""
        if not documents or not embeddings:
            return
            
        if len(documents) != len(embeddings):
            raise ValueError(f"Document count ({len(documents)}) doesn't match embedding count ({len(embeddings)})")
        
        dimension = len(embeddings[0])
        if dimension == 0:
            raise ValueError("Embedding dimension is 0")
        
        # Reset collection cache to ensure we get the right one
        self._collection = None
        collection = self._get_collection(dimension)
        
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [
            {k: v for k, v in doc.get("metadata", {}).items() if v is not None}
            for doc in documents
        ]

        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Adding {len(documents)} documents to ChromaDB collection '{self.collection_name}'")
            
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
            
            # Verify they were added
            count_after = collection.count()
            logger.debug(f"Collection now has {count_after} documents")
            
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"ChromaDB add failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        collection = self._get_collection(len(query_embedding))
        
        where = filter_dict if filter_dict else None
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
        )

        documents = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i, doc_id in enumerate(results["ids"][0]):
                documents.append({
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": 1 - results["distances"][0][i] if results["distances"] else 0.0,
                })

        return documents

    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from ChromaDB."""
        collection = self._get_collection(384)  # Dimension doesn't matter for delete
        collection.delete(ids=document_ids)

    def delete_all(self) -> None:
        """Delete all documents from ChromaDB."""
        client = self._get_client()
        try:
            client.delete_collection(self.collection_name)
            self._collection = None
        except Exception:
            pass  # Collection might not exist

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            client = self._get_client()
            try:
                # Try to get existing collection
                collection = client.get_collection(self.collection_name)
                count = collection.count()
                
                # Also try to get a sample to verify
                if count > 0:
                    try:
                        sample = collection.get(limit=1)
                        has_data = bool(sample.get("ids") and len(sample["ids"]) > 0)
                        if not has_data:
                            # Collection exists but has no data
                            return {"document_count": 0}
                    except Exception:
                        pass
                
                return {"document_count": count}
            except Exception as e:
                # Collection doesn't exist yet
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Collection '{self.collection_name}' doesn't exist: {str(e)}")
                return {"document_count": 0}
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Error getting stats: {str(e)}")
            return {"document_count": 0}
