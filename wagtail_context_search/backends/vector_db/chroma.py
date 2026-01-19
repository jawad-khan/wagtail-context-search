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
        self._client = None
        self._collection = None

    def _get_client(self):
        """Lazy load ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings

                if self.persist_directory:
                    self._client = chromadb.PersistentClient(
                        path=self.persist_directory
                    )
                else:
                    self._client = chromadb.Client(Settings(anonymized_telemetry=False))
            except ImportError:
                raise ImportError(
                    "chromadb package is required. Install with: pip install chromadb"
                )
        return self._client

    def _get_collection(self, dimension: int):
        """Get or create collection."""
        if self._collection is None:
            client = self._get_client()
            try:
                self._collection = client.get_collection(self.collection_name)
            except Exception:
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
        collection = self._get_collection(len(embeddings[0]) if embeddings else 384)
        
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [
            {k: v for k, v in doc.get("metadata", {}).items() if v is not None}
            for doc in documents
        ]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

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
            collection = self._get_collection(384)
            count = collection.count()
            return {"document_count": count}
        except Exception:
            return {"document_count": 0}
