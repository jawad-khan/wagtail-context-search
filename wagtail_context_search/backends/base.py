"""
Abstract base classes for pluggable backends.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseLLMBackend(ABC):
    """Abstract base class for LLM backends."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the LLM backend with configuration."""
        self.config = config
        self.model = config.get("LLM_MODEL", "gpt-4o-mini")
        self.temperature = config.get("LLM_TEMPERATURE", 0.7)
        self.max_tokens = config.get("LLM_MAX_TOKENS", 1000)
        self.backend_settings = config.get("BACKEND_SETTINGS", {}).get(
            self.__class__.__name__.lower().replace("backend", ""), {}
        )

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The user prompt/question
            system_prompt: Optional system prompt for context
            **kwargs: Additional backend-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is available and configured."""
        pass

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Generate a streaming response (optional).

        Should yield chunks of text as they are generated.
        """
        # Default implementation: return non-streaming result
        result = self.generate(prompt, system_prompt, **kwargs)
        yield result


class BaseEmbedder(ABC):
    """Abstract base class for embedding backends."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the embedder with configuration."""
        self.config = config
        self.backend_settings = config.get("BACKEND_SETTINGS", {}).get(
            self.__class__.__name__.lower().replace("embedder", ""), {}
        )

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (more efficient).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this embedder."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the embedder is available and configured."""
        pass


class BaseVectorDB(ABC):
    """Abstract base class for vector database backends."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the vector DB with configuration."""
        self.config = config
        self.collection_name = config.get("VECTOR_DB_COLLECTION", "wagtail_content")
        self.backend_settings = config.get("BACKEND_SETTINGS", {}).get(
            self.__class__.__name__.lower().replace("vectordb", ""), {}
        )

    @abstractmethod
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> None:
        """
        Add documents to the vector database.

        Args:
            documents: List of document dicts with at least 'id' and 'text' keys
            embeddings: List of embedding vectors corresponding to documents
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            List of document dicts with 'id', 'text', 'metadata', 'score'
        """
        pass

    @abstractmethod
    def delete_documents(self, document_ids: List[str]) -> None:
        """
        Delete documents from the vector database.

        Args:
            document_ids: List of document IDs to delete
        """
        pass

    @abstractmethod
    def delete_all(self) -> None:
        """Delete all documents from the vector database."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the vector DB is available and configured."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database (optional)."""
        return {}
