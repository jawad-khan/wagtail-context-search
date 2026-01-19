"""
OpenAI LLM backend implementation.
"""

import os
from typing import Any, Dict, Optional

from wagtail_context_search.backends.llm.base import BaseLLMBackend


class OpenAIBackend(BaseLLMBackend):
    """OpenAI LLM backend using OpenAI API."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI backend."""
        super().__init__(config)
        self.api_key = self.backend_settings.get(
            "api_key"
        ) or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY env var or in config.")

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return self.api_key is not None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate response using OpenAI API."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            )

            return response.choices[0].message.content.strip()
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ):
        """Generate streaming response using OpenAI API."""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            stream = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")
