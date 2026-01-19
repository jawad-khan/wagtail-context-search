"""
Qdrant vector database backend implementation.
"""

import os
from typing import Any, Dict, List, Optional

from wagtail_context_search.backends.vector_db.base import BaseVectorDB


class QdrantBackend(BaseVectorDB):
    """Qdrant vector database backend."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Qdrant backend."""
        super().__init__(config)
        self.url = self.backend_settings.get("url", "http://localhost:6333")
        self.api_key = self.backend_settings.get("api_key") or os.getenv("QDRANT_API_KEY")
        self._client = None

    def _get_client(self):
        """Lazy load Qdrant client."""
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.models import Distance, VectorParams

                self._client = QdrantClient(
                    url=self.url,
                    api_key=self.api_key,
                )
            except ImportError:
                raise ImportError(
                    "qdrant-client package is required. Install with: pip install qdrant-client"
                )
        return self._client

    def _ensure_collection(self, dimension: int):
        """Ensure the collection exists."""
        client = self._get_client()
        try:
            from qdrant_client.models import Distance, VectorParams

            try:
                client.get_collection(self.collection_name)
            except Exception:
                client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=dimension,
                        distance=Distance.COSINE,
                    ),
                )
        except Exception as e:
            raise RuntimeError(f"Failed to ensure Qdrant collection: {str(e)}")

    def is_available(self) -> bool:
        """Check if Qdrant is available."""
        try:
            client = self._get_client()
            client.get_collections()
            return True
        except Exception:
            return False

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> None:
        """Add documents to Qdrant."""
        if not documents or not embeddings:
            return
            
        dimension = len(embeddings[0])
        self._ensure_collection(dimension)
        
        client = self._get_client()
        
        try:
            from qdrant_client.models import PointStruct

            points = []
            for doc, embedding in zip(documents, embeddings):
                points.append(
                    PointStruct(
                        id=doc["id"],
                        vector=embedding,
                        payload={
                            "text": doc["text"],
                            **doc.get("metadata", {}),
                        },
                    )
                )

            client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to add documents to Qdrant: {str(e)}")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        client = self._get_client()
        
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            query_filter = None
            if filter_dict:
                conditions = []
                for key, value in filter_dict.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value),
                        )
                    )
                if conditions:
                    query_filter = Filter(must=conditions)

            results = client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter,
            )

            documents = []
            for result in results:
                payload = result.payload or {}
                documents.append({
                    "id": str(result.id),
                    "text": payload.get("text", ""),
                    "metadata": {k: v for k, v in payload.items() if k != "text"},
                    "score": result.score,
                })

            return documents
        except Exception as e:
            raise RuntimeError(f"Failed to search Qdrant: {str(e)}")

    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from Qdrant."""
        client = self._get_client()
        
        try:
            client.delete(
                collection_name=self.collection_name,
                points_selector=document_ids,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to delete documents from Qdrant: {str(e)}")

    def delete_all(self) -> None:
        """Delete all documents from Qdrant."""
        client = self._get_client()
        try:
            client.delete_collection(self.collection_name)
        except Exception:
            pass  # Collection might not exist

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            client = self._get_client()
            collection_info = client.get_collection(self.collection_name)
            return {"document_count": collection_info.points_count}
        except Exception:
            return {"document_count": 0}
