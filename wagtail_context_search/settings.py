"""
Default settings for Wagtail Context Search.

These can be overridden in your Django settings.py file.
"""

from django.conf import settings

# Default configuration
DEFAULT_CONFIG = {
    # LLM Configuration
    "LLM_BACKEND": "openai",  # Options: openai, anthropic, ollama
    "LLM_MODEL": "gpt-4o-mini",  # Model name (varies by backend)
    "LLM_TEMPERATURE": 0.7,
    "LLM_MAX_TOKENS": 1000,
    
    # Embedding Configuration
    "EMBEDDER_BACKEND": "openai",  # Options: openai, sentence_transformers
    "EMBEDDER_MODEL": "text-embedding-3-small",  # For OpenAI
    "EMBEDDING_DIMENSION": 1536,  # Default for OpenAI
    
    # Vector Database Configuration
    "VECTOR_DB_BACKEND": "chroma",  # Options: chroma, pgvector, qdrant
    "VECTOR_DB_COLLECTION": "wagtail_content",
    
    # Retrieval Configuration
    "TOP_K": 5,  # Number of chunks to retrieve
    "CHUNK_SIZE": 512,  # Characters per chunk
    "CHUNK_OVERLAP": 50,  # Overlap between chunks
    
    # Assistant UI Configuration
    "ASSISTANT_ENABLED": True,
    "ASSISTANT_POSITION": "bottom-right",  # bottom-right, bottom-left
    "ASSISTANT_THEME": "light",  # light, dark
    "ASSISTANT_UI_MODE": "both",  # chat, search, both
    
    # Page Types to Index
    "PAGE_TYPES": [],  # Empty list means index all page types
    
    # Prompt Template
    "PROMPT_TEMPLATE": None,  # None uses default template
    
    # API Configuration
    "API_RATE_LIMIT": None,  # Requests per minute (None = no limit)
    "API_REQUIRE_AUTH": False,
    
    # Backend-specific settings
    "BACKEND_SETTINGS": {
        "openai": {
            "api_key": None,  # Set via OPENAI_API_KEY env var
        },
        "anthropic": {
            "api_key": None,  # Set via ANTHROPIC_API_KEY env var
        },
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "llama3.2:latest",
        },
        "sentence_transformers": {
            "model_name": "all-MiniLM-L6-v2",
            "device": "cpu",
        },
        "chroma": {
            "persist_directory": None,  # None = in-memory
        },
        "pgvector": {
            "connection_string": None,  # Uses Django DB if None
        },
        "qdrant": {
            "url": "http://localhost:6333",
            "api_key": None,
        },
    },
}


def get_config():
    """Get configuration from Django settings or use defaults."""
    user_config = getattr(settings, "WAGTAIL_CONTEXT_SEARCH", {})
    config = DEFAULT_CONFIG.copy()
    
    # Deep merge backend settings
    if "BACKEND_SETTINGS" in user_config:
        config["BACKEND_SETTINGS"] = {
            **config["BACKEND_SETTINGS"],
            **user_config["BACKEND_SETTINGS"],
        }
        del user_config["BACKEND_SETTINGS"]
    
    # Merge remaining settings
    config.update(user_config)
    return config
