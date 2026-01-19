"""
OpenAI embedding backend implementation.
"""

import os
from typing import Any, Dict, List

from wagtail_context_search.backends.embedder.base import BaseEmbedder


class OpenAIEmbedder(BaseEmbedder):
    """OpenAI embedding backend."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI embedder."""
        super().__init__(config)
        self.api_key = self.backend_settings.get(
            "api_key"
        ) or os.getenv("OPENAI_API_KEY")
        self.model = config.get("EMBEDDER_MODEL", "text-embedding-3-small")
        self.dimension = config.get("EMBEDDING_DIMENSION", 1536)
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY env var or in config."
            )

    def is_available(self) -> bool:
        """Check if OpenAI embedder is available."""
        return self.api_key is not None

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            response = client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimension,
            )

            return [item.embedding for item in response.data]
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI embedding API error: {str(e)}")
