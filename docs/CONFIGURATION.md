# Configuration Reference

Complete reference for configuring Wagtail Context Search.

## Quick Setup

**Minimal configuration (automatic widget injection):**

1. Add middleware to `MIDDLEWARE`:
   ```python
   MIDDLEWARE = [
       # ... your existing middleware ...
       'wagtail_context_search.middleware.RAGAssistantMiddleware',
   ]
   ```

2. Configure `WAGTAIL_CONTEXT_SEARCH` in settings (see below)

3. That's it! The widget appears automatically on all pages (if `ASSISTANT_ENABLED: True`)

**No template or URL changes needed!**

## Basic Configuration

Add `WAGTAIL_CONTEXT_SEARCH` to your `settings.py`:

```python
WAGTAIL_CONTEXT_SEARCH = {
    # Your configuration here
}
```

## LLM Configuration

### LLM Backend Selection

Choose which LLM provider to use:

```python
WAGTAIL_CONTEXT_SEARCH = {
    "LLM_BACKEND": "openai",  # Options: openai, anthropic, ollama
    "LLM_MODEL": "gpt-4o-mini",
    "LLM_TEMPERATURE": 0.7,
    "LLM_MAX_TOKENS": 1000,
}
```

### OpenAI Configuration

```python
WAGTAIL_CONTEXT_SEARCH = {
    "LLM_BACKEND": "openai",
    "LLM_MODEL": "gpt-4o-mini",  # or gpt-3.5-turbo, gpt-4, etc.
    "BACKEND_SETTINGS": {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
    },
}
```

### Anthropic Configuration

```python
WAGTAIL_CONTEXT_SEARCH = {
    "LLM_BACKEND": "anthropic",
    "LLM_MODEL": "claude-3-5-sonnet-20241022",
    "BACKEND_SETTINGS": {
        "anthropic": {
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        },
    },
}
```

### Ollama Configuration

```python
WAGTAIL_CONTEXT_SEARCH = {
    "LLM_BACKEND": "ollama",
    "LLM_MODEL": "llama2",  # Model name in Ollama
    "BACKEND_SETTINGS": {
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "llama2",
        },
    },
}
```

## Embedding Configuration

### Embedder Backend Selection

```python
WAGTAIL_CONTEXT_SEARCH = {
    "EMBEDDER_BACKEND": "openai",  # Options: openai, sentence_transformers
    "EMBEDDER_MODEL": "text-embedding-3-small",
    "EMBEDDING_DIMENSION": 1536,
}
```

### OpenAI Embeddings

```python
WAGTAIL_CONTEXT_SEARCH = {
    "EMBEDDER_BACKEND": "openai",
    "EMBEDDER_MODEL": "text-embedding-3-small",  # or text-embedding-3-large
    "EMBEDDING_DIMENSION": 1536,
    "BACKEND_SETTINGS": {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
    },
}
```

### Sentence Transformers

```python
WAGTAIL_CONTEXT_SEARCH = {
    "EMBEDDER_BACKEND": "sentence_transformers",
    "BACKEND_SETTINGS": {
        "sentence_transformers": {
            "model_name": "all-MiniLM-L6-v2",  # or other models
            "device": "cpu",  # or "cuda" for GPU
        },
    },
}
```

## Vector Database Configuration

### ChromaDB

```python
WAGTAIL_CONTEXT_SEARCH = {
    "VECTOR_DB_BACKEND": "chroma",
    "VECTOR_DB_COLLECTION": "wagtail_content",
    "BACKEND_SETTINGS": {
        "chroma": {
            "persist_directory": "/path/to/chroma/db",  # None for in-memory
        },
    },
}
```

### Meilisearch

```python
WAGTAIL_CONTEXT_SEARCH = {
    "VECTOR_DB_BACKEND": "meilisearch",
    "VECTOR_DB_COLLECTION": "wagtail_content",
    "BACKEND_SETTINGS": {
        "meilisearch": {
            "url": "http://localhost:7700",
            "api_key": os.getenv("MEILISEARCH_API_KEY"),  # Optional
        },
    },
}
```

### PostgreSQL with pgvector

```python
WAGTAIL_CONTEXT_SEARCH = {
    "VECTOR_DB_BACKEND": "pgvector",
    "VECTOR_DB_COLLECTION": "wagtail_content",
    "BACKEND_SETTINGS": {
        "pgvector": {
            "connection_string": None,  # Uses Django DB connection if None
        },
    },
}
```

**Note**: You need to install the pgvector extension in PostgreSQL:
```sql
CREATE EXTENSION vector;
```

### Qdrant

```python
WAGTAIL_CONTEXT_SEARCH = {
    "VECTOR_DB_BACKEND": "qdrant",
    "VECTOR_DB_COLLECTION": "wagtail_content",
    "BACKEND_SETTINGS": {
        "qdrant": {
            "url": "http://localhost:6333",
            "api_key": os.getenv("QDRANT_API_KEY"),  # Optional
        },
    },
}
```

## Retrieval Configuration

```python
WAGTAIL_CONTEXT_SEARCH = {
    "TOP_K": 5,  # Number of chunks to retrieve
    "CHUNK_SIZE": 512,  # Characters per chunk
    "CHUNK_OVERLAP": 50,  # Overlap between chunks
}
```

## Assistant UI Configuration

```python
WAGTAIL_CONTEXT_SEARCH = {
    "ASSISTANT_ENABLED": True,  # Enable/disable the widget (middleware respects this)
    "ASSISTANT_POSITION": "bottom-right",  # bottom-right, bottom-left
    "ASSISTANT_THEME": "light",  # light, dark
    "ASSISTANT_UI_MODE": "both",  # chat, search, both
}
```

**Note:** When `ASSISTANT_ENABLED: False`, the widget will not appear on pages, but the API endpoints (`/rag/query/`, `/rag/health/`) will still work for programmatic access.

## Page Type Filtering

Only index specific page types:

```python
WAGTAIL_CONTEXT_SEARCH = {
    "PAGE_TYPES": [
        "BlogPage",
        "ArticlePage",
        "DocumentPage",
    ],
}
```

Leave empty list `[]` to index all page types.

## Prompt Template

Customize the prompt template:

```python
WAGTAIL_CONTEXT_SEARCH = {
    "PROMPT_TEMPLATE": """Context from website:

{context}

Question: {question}

Please provide a helpful answer based on the context above.""",
}
```

## API Configuration

```python
WAGTAIL_CONTEXT_SEARCH = {
    "API_RATE_LIMIT": 60,  # Requests per minute (None = no limit)
    "API_REQUIRE_AUTH": False,  # Require authentication for API
}
```

## Middleware Configuration

The middleware automatically handles widget injection and API endpoints. Just add it to your `MIDDLEWARE`:

```python
MIDDLEWARE = [
    # ... your existing middleware ...
    'wagtail_context_search.middleware.RAGAssistantMiddleware',
]
```

**What the middleware does:**
- Automatically injects the widget into all HTML pages (if `ASSISTANT_ENABLED: True`)
- Handles `/rag/query/` and `/rag/health/` API endpoints automatically
- Skips admin pages, API endpoints, and `/rag/` paths to avoid conflicts
- Respects `ASSISTANT_ENABLED` setting to show/hide the widget

**No template or URL changes needed!**

## Complete Example

```python
import os

# In settings.py

# Add middleware
MIDDLEWARE = [
    # ... your existing middleware ...
    'wagtail_context_search.middleware.RAGAssistantMiddleware',
]

# Configure the plugin
WAGTAIL_CONTEXT_SEARCH = {
    # LLM Configuration
    "LLM_BACKEND": "openai",
    "LLM_MODEL": "gpt-4o-mini",
    "LLM_TEMPERATURE": 0.7,
    "LLM_MAX_TOKENS": 1000,
    
    # Embedding Configuration
    "EMBEDDER_BACKEND": "openai",
    "EMBEDDER_MODEL": "text-embedding-3-small",
    "EMBEDDING_DIMENSION": 1536,
    
    # Vector Database Configuration
    "VECTOR_DB_BACKEND": "chroma",
    "VECTOR_DB_COLLECTION": "wagtail_content",
    
    # Retrieval Configuration
    "TOP_K": 5,
    "CHUNK_SIZE": 512,
    "CHUNK_OVERLAP": 50,
    
    # Assistant UI Configuration
    "ASSISTANT_ENABLED": True,  # Widget appears automatically
    "ASSISTANT_POSITION": "bottom-right",
    "ASSISTANT_THEME": "light",
    "ASSISTANT_UI_MODE": "both",
    
    # Page Types (empty = all types)
    "PAGE_TYPES": [],
    
    # Backend-specific settings
    "BACKEND_SETTINGS": {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
        "chroma": {
            "persist_directory": None,  # In-memory
        },
    },
}
```

## Environment Variables

Recommended: Use environment variables for sensitive data:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export QDRANT_API_KEY="..."
export MEILISEARCH_API_KEY="..."  # If using Meilisearch
```

Then reference in settings:

```python
"BACKEND_SETTINGS": {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
}
```

## Troubleshooting Configuration

### Widget Not Appearing

If the widget doesn't appear:

1. **Check middleware is added**: Ensure `'wagtail_context_search.middleware.RAGAssistantMiddleware'` is in your `MIDDLEWARE` list
2. **Check `ASSISTANT_ENABLED`**: Verify it's set to `True` in your configuration
3. **Check static files**: Run `python manage.py collectstatic` to ensure CSS/JS files are available
4. **Check browser console**: Look for JavaScript errors
5. **Verify page structure**: The middleware requires a `</body>` tag in your HTML

### Settings Not Loading from `local.py` or Custom Settings Files

If you're using a Django settings structure with separate files (e.g., `base.py`, `local.py`), ensure that:

1. **Your settings module is correctly configured**: Make sure `DJANGO_SETTINGS_MODULE` points to the correct settings file, or that your main settings file imports from `local.py`:

```python
# In your main settings.py or base.py
try:
    from .local import *
except ImportError:
    pass
```

2. **Configuration is in the right place**: The `WAGTAIL_CONTEXT_SEARCH` dictionary should be in the settings file that Django actually loads.

3. **Check configuration is loaded**: Run the debug command to verify:

```bash
python manage.py rag_debug
```

This will show:
- Whether user configuration is present
- Which backends are configured
- Whether API keys are set (masked for security)

4. **Deep merge for nested settings**: The plugin automatically merges `BACKEND_SETTINGS` with defaults. If you only specify:

```python
WAGTAIL_CONTEXT_SEARCH = {
    "BACKEND_SETTINGS": {
        "openai": {
            "api_key": "sk-...",
        },
    },
}
```

The plugin will merge this with default settings, so you don't need to specify all backend settings.

### Verifying API Keys Are Loaded

If API keys aren't being picked up:

1. **Check environment variables**: Ensure environment variables are set before Django starts:
   ```bash
   export OPENAI_API_KEY="sk-..."
   python manage.py runserver
   ```

2. **Check settings file**: Verify the configuration is in the settings file Django loads:
   ```python
   # In Django shell
   from django.conf import settings
   print(settings.WAGTAIL_CONTEXT_SEARCH)
   ```

3. **Use debug command**: Run `python manage.py rag_debug` to see the actual configuration being used.

## Multi-Site Configuration

For multi-site setups, you can configure per-site settings using Wagtail's site settings or override in your site's settings module.
