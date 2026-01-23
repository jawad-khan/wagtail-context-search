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
        "meilisearch": {
            "url": "http://localhost:7700",
            "api_key": None,
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
    
    # Deep merge backend settings - ensure nested dicts are merged correctly
    if "BACKEND_SETTINGS" in user_config:
        # Start with default backend settings
        merged_backend_settings = config["BACKEND_SETTINGS"].copy()
        # Merge user backend settings, ensuring nested dicts are merged
        for backend_name, backend_config in user_config["BACKEND_SETTINGS"].items():
            if backend_name in merged_backend_settings:
                # Merge nested dict if both exist
                if isinstance(merged_backend_settings[backend_name], dict) and isinstance(backend_config, dict):
                    merged_backend_settings[backend_name] = {
                        **merged_backend_settings[backend_name],
                        **backend_config,
                    }
                else:
                    # Replace if not both dicts
                    merged_backend_settings[backend_name] = backend_config
            else:
                # New backend setting
                merged_backend_settings[backend_name] = backend_config
        config["BACKEND_SETTINGS"] = merged_backend_settings
        # Remove from user_config so it doesn't override
        user_config = {k: v for k, v in user_config.items() if k != "BACKEND_SETTINGS"}
    
    # Merge remaining settings
    config.update(user_config)
    return config


def debug_config():
    """Debug helper to print current configuration (without sensitive data)."""
    import logging
    logger = logging.getLogger(__name__)
    
    user_config = getattr(settings, "WAGTAIL_CONTEXT_SEARCH", {})
    config = get_config()
    
    logger.info("=== Wagtail Context Search Configuration Debug ===")
    logger.info(f"User config present: {bool(user_config)}")
    logger.info(f"LLM Backend: {config.get('LLM_BACKEND')}")
    logger.info(f"Embedder Backend: {config.get('EMBEDDER_BACKEND')}")
    logger.info(f"Vector DB Backend: {config.get('VECTOR_DB_BACKEND')}")
    
    # Check backend settings (mask API keys)
    backend_settings = config.get("BACKEND_SETTINGS", {})
    for backend_name, backend_config in backend_settings.items():
        if isinstance(backend_config, dict):
            api_key = backend_config.get("api_key")
            if api_key:
                masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
                logger.info(f"  {backend_name}.api_key: {masked_key} (present)")
            else:
                logger.info(f"  {backend_name}.api_key: None (missing)")
    
    logger.info("==================================================")
