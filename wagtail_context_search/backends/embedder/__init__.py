"""
Embedding backend implementations.
"""

from wagtail_context_search.backends.embedder.base import BaseEmbedder
from wagtail_context_search.backends.embedder.openai import OpenAIEmbedder
from wagtail_context_search.backends.embedder.sentence_transformers import (
    SentenceTransformersEmbedder,
)

__all__ = [
    "BaseEmbedder",
    "OpenAIEmbedder",
    "SentenceTransformersEmbedder",
]

# Registry for backend selection
EMBEDDER_BACKENDS = {
    "openai": OpenAIEmbedder,
    "sentence_transformers": SentenceTransformersEmbedder,
}


def get_embedder_backend(backend_name: str, config: dict):
    """Get an embedder backend instance by name."""
    backend_class = EMBEDDER_BACKENDS.get(backend_name.lower())
    if not backend_class:
        raise ValueError(f"Unknown embedder backend: {backend_name}")
    return backend_class(config)
