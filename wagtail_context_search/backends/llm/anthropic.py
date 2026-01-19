"""
Anthropic (Claude) LLM backend implementation.
"""

import os
from typing import Any, Dict, Optional

from wagtail_context_search.backends.llm.base import BaseLLMBackend


class AnthropicBackend(BaseLLMBackend):
    """Anthropic Claude LLM backend."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Anthropic backend."""
        super().__init__(config)
        self.api_key = self.backend_settings.get(
            "api_key"
        ) or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY env var or in config."
            )

    def is_available(self) -> bool:
        """Check if Anthropic is available."""
        return self.api_key is not None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate response using Anthropic API."""
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=self.api_key)
            
            messages = [{"role": "user", "content": prompt}]
            
            response = client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                system=system_prompt or "",
                messages=messages,
            )

            return response.content[0].text.strip()
        except ImportError:
            raise ImportError(
                "anthropic package is required. Install with: pip install anthropic"
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ):
        """Generate streaming response using Anthropic API."""
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=self.api_key)
            
            messages = [{"role": "user", "content": prompt}]
            
            with client.messages.stream(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                system=system_prompt or "",
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except ImportError:
            raise ImportError(
                "anthropic package is required. Install with: pip install anthropic"
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")
