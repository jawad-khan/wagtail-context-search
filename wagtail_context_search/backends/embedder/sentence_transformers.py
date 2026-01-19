"""
Sentence Transformers embedding backend implementation.
"""

from typing import Any, Dict, List

from wagtail_context_search.backends.embedder.base import BaseEmbedder


class SentenceTransformersEmbedder(BaseEmbedder):
    """Sentence Transformers embedding backend for local models."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Sentence Transformers embedder."""
        super().__init__(config)
        self.model_name = self.backend_settings.get(
            "model_name", "all-MiniLM-L6-v2"
        )
        self.device = self.backend_settings.get("device", "cpu")
        self._model = None
        self._dimension = None

    def _get_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name, device=self.device)
                # Get dimension from model
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers package is required. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def is_available(self) -> bool:
        """Check if Sentence Transformers is available."""
        try:
            self._get_model()
            return True
        except Exception:
            return False

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        if self._dimension is None:
            self._get_model()
        return self._dimension

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
