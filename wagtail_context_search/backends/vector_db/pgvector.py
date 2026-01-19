"""
PostgreSQL with pgvector backend implementation.
"""

from typing import Any, Dict, List, Optional

from django.db import connection
from django.db.utils import OperationalError

from wagtail_context_search.backends.vector_db.base import BaseVectorDB


class PGVectorBackend(BaseVectorDB):
    """PostgreSQL with pgvector extension backend."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize pgvector backend."""
        super().__init__(config)
        self.connection_string = self.backend_settings.get("connection_string")
        self._table_name = f"{self.collection_name}_vectors"
        self._dimension = None

    def _ensure_extension(self):
        """Ensure pgvector extension is installed."""
        with connection.cursor() as cursor:
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            except Exception:
                pass  # Extension might already exist or not available

    def _ensure_table(self, dimension: int):
        """Ensure the vector table exists."""
        self._dimension = dimension
        self._ensure_extension()
        
        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    id VARCHAR(255) PRIMARY KEY,
                    text TEXT NOT NULL,
                    embedding vector({dimension}),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create index for vector similarity search
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {self._table_name}_embedding_idx 
                ON {self._table_name} 
                USING ivfflat (embedding vector_cosine_ops);
            """)

    def is_available(self) -> bool:
        """Check if pgvector is available."""
        try:
            self._ensure_extension()
            return True
        except Exception:
            return False

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> None:
        """Add documents to pgvector."""
        if not documents or not embeddings:
            return
            
        dimension = len(embeddings[0])
        self._ensure_table(dimension)
        
        with connection.cursor() as cursor:
            for doc, embedding in zip(documents, embeddings):
                import json
                metadata = json.dumps(doc.get("metadata", {}))
                
                cursor.execute(f"""
                    INSERT INTO {self._table_name} (id, text, embedding, metadata)
                    VALUES (%s, %s, %s::vector, %s::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                        text = EXCLUDED.text,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata;
                """, [doc["id"], doc["text"], str(embedding), metadata])

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        dimension = len(query_embedding)
        self._ensure_table(dimension)
        
        with connection.cursor() as cursor:
            embedding_str = str(query_embedding)
            
            # Build WHERE clause for filters
            where_clause = ""
            params = [embedding_str, top_k]
            
            if filter_dict:
                conditions = []
                for key, value in filter_dict.items():
                    conditions.append(f"metadata->>%s = %s")
                    params.extend([key, str(value)])
                where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                SELECT id, text, metadata, 
                       1 - (embedding <=> %s::vector) as score
                FROM {self._table_name}
                {where_clause}
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            documents = []
            for row in results:
                import json
                documents.append({
                    "id": row[0],
                    "text": row[1],
                    "metadata": json.loads(row[2]) if row[2] else {},
                    "score": float(row[3]),
                })
            
            return documents

    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from pgvector."""
        if not document_ids:
            return
            
        with connection.cursor() as cursor:
            placeholders = ",".join(["%s"] * len(document_ids))
            cursor.execute(
                f"DELETE FROM {self._table_name} WHERE id IN ({placeholders})",
                document_ids
            )

    def delete_all(self) -> None:
        """Delete all documents from pgvector."""
        with connection.cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {self._table_name};")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the table."""
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {self._table_name};")
                count = cursor.fetchone()[0]
                return {"document_count": count}
        except Exception:
            return {"document_count": 0}
