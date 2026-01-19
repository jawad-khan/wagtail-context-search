# Configuration Reference

Complete reference for configuring Wagtail Context Search.

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
    "ASSISTANT_ENABLED": True,
    "ASSISTANT_POSITION": "bottom-right",  # bottom-right, bottom-left
    "ASSISTANT_THEME": "light",  # light, dark
    "ASSISTANT_UI_MODE": "both",  # chat, search, both
}
```

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

## Complete Example

```python
import os

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
    "ASSISTANT_ENABLED": True,
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
```

Then reference in settings:

```python
"BACKEND_SETTINGS": {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
}
```

## Multi-Site Configuration

For multi-site setups, you can configure per-site settings using Wagtail's site settings or override in your site's settings module.
