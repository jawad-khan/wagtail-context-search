"""
LLM backend implementations.
"""

from wagtail_context_search.backends.llm.anthropic import AnthropicBackend
from wagtail_context_search.backends.llm.base import BaseLLMBackend
from wagtail_context_search.backends.llm.ollama import OllamaBackend
from wagtail_context_search.backends.llm.openai import OpenAIBackend

__all__ = [
    "BaseLLMBackend",
    "OpenAIBackend",
    "AnthropicBackend",
    "OllamaBackend",
]

# Registry for backend selection
LLM_BACKENDS = {
    "openai": OpenAIBackend,
    "anthropic": AnthropicBackend,
    "ollama": OllamaBackend,
}


def get_llm_backend(backend_name: str, config: dict):
    """Get an LLM backend instance by name."""
    backend_class = LLM_BACKENDS.get(backend_name.lower())
    if not backend_class:
        raise ValueError(f"Unknown LLM backend: {backend_name}")
    return backend_class(config)
