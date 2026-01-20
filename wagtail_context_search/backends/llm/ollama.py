"""
Ollama LLM backend implementation for local models.
"""

import os
from typing import Any, Dict, Optional

from wagtail_context_search.backends.llm.base import BaseLLMBackend


class OllamaBackend(BaseLLMBackend):
    """Ollama LLM backend for local models."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Ollama backend."""
        super().__init__(config)
        self.base_url = self.backend_settings.get(
            "base_url", "http://localhost:11434"
        )
        self.model = self.backend_settings.get("model", self.model)

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            import requests

            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                # Also check if the model exists
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                if self.model not in model_names:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Ollama model '{self.model}' not found. Available models: {model_names}")
                    return False
                return True
            return False
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Ollama availability check failed: {str(e)}")
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate response using Ollama API."""
        try:
            import requests

            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", self.temperature),
                        "num_predict": kwargs.get("max_tokens", self.max_tokens),
                    },
                },
                timeout=60,
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except ImportError:
            raise ImportError(
                "requests package is required. Install with: pip install requests"
            )
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {str(e)}")

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ):
        """Generate streaming response using Ollama API."""
        try:
            import requests

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Try chat API first
            try:
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": True,
                        "options": {
                            "temperature": kwargs.get("temperature", self.temperature),
                            "num_predict": kwargs.get("max_tokens", self.max_tokens),
                        },
                    },
                    stream=True,
                    timeout=60,
                )
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        import json
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                        elif "response" in data:
                            yield data["response"]
            except requests.exceptions.HTTPError as e:
                # Fallback to generate API
                if e.response.status_code == 404:
                    full_prompt = prompt
                    if system_prompt:
                        full_prompt = f"{system_prompt}\n\n{prompt}"

                    response = requests.post(
                        f"{self.base_url}/api/generate",
                        json={
                            "model": self.model,
                            "prompt": full_prompt,
                            "stream": True,
                            "options": {
                                "temperature": kwargs.get("temperature", self.temperature),
                                "num_predict": kwargs.get("max_tokens", self.max_tokens),
                            },
                        },
                        stream=True,
                        timeout=60,
                    )
                    response.raise_for_status()

                    for line in response.iter_lines():
                        if line:
                            import json
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                else:
                    raise
        except ImportError:
            raise ImportError(
                "requests package is required. Install with: pip install requests"
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ollama API error: {str(e)}")
            raise RuntimeError(f"Ollama API error: {str(e)}")
