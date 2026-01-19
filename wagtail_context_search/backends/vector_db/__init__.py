"""
Vector database backend implementations.
"""

from wagtail_context_search.backends.vector_db.base import BaseVectorDB
from wagtail_context_search.backends.vector_db.chroma import ChromaBackend
from wagtail_context_search.backends.vector_db.pgvector import PGVectorBackend
from wagtail_context_search.backends.vector_db.qdrant import QdrantBackend

__all__ = [
    "BaseVectorDB",
    "ChromaBackend",
    "PGVectorBackend",
    "QdrantBackend",
]

# Registry for backend selection
VECTOR_DB_BACKENDS = {
    "chroma": ChromaBackend,
    "pgvector": PGVectorBackend,
    "qdrant": QdrantBackend,
}


def get_vector_db_backend(backend_name: str, config: dict):
    """Get a vector DB backend instance by name."""
    backend_class = VECTOR_DB_BACKENDS.get(backend_name.lower())
    if not backend_class:
        raise ValueError(f"Unknown vector DB backend: {backend_name}")
    return backend_class(config)
