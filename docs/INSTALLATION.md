# Installation Guide

This guide will help you install and set up Wagtail Context Search.

## Prerequisites

- Python 3.10 or higher
- Django 4.2 or higher
- Wagtail 7.0 or higher
- A Wagtail site already set up

## Step 1: Install the Package

Install using pip:

```bash
pip install wagtail-context-search
```

Or install from source:

```bash
git clone https://github.com/yourusername/wagtail-context-search.git
cd wagtail-context-search
pip install -e .
```

## Step 2: Install Backend Dependencies

Install the dependencies for the backends you want to use:

### For OpenAI
```bash
pip install openai
```

### For Anthropic
```bash
pip install anthropic
```

### For Ollama
```bash
pip install requests
# Also install Ollama locally: https://ollama.ai
```

### For Sentence Transformers
```bash
pip install sentence-transformers torch
```

### For ChromaDB
```bash
pip install chromadb
```

### For PostgreSQL with pgvector
```bash
pip install psycopg2-binary
# Also install pgvector extension in PostgreSQL
```

### For Qdrant
```bash
pip install qdrant-client
# Or run Qdrant server: https://qdrant.tech/documentation/quick-start/
```

## Step 3: Add to INSTALLED_APPS

Add `wagtail_context_search` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'wagtail_context_search',
]
```

## Step 4: Add Middleware (Automatic Widget Injection)

Add the middleware to automatically inject the widget and handle API endpoints:

```python
MIDDLEWARE = [
    # ... your existing middleware ...
    'wagtail_context_search.middleware.RAGAssistantMiddleware',
]
```

**This middleware automatically:**
- Injects the assistant widget into all HTML pages (if `ASSISTANT_ENABLED: True`)
- Handles `/rag/query/` and `/rag/health/` API endpoints (no URL configuration needed)
- Respects the `ASSISTANT_ENABLED` setting to show/hide the widget

**No need to:**
- Edit `base.html` or any templates
- Add URLs to `urls.py`
- Add template tags

## Step 5: Run Migrations

Create and apply database migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Step 6: Configure Settings

Add configuration to your `settings.py`. See [CONFIGURATION.md](CONFIGURATION.md) for details.

Minimum configuration:

```python
WAGTAIL_CONTEXT_SEARCH = {
    "LLM_BACKEND": "openai",
    "EMBEDDER_BACKEND": "openai",
    "VECTOR_DB_BACKEND": "chroma",
    "BACKEND_SETTINGS": {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
    },
}
```

## Step 7: Set Environment Variables

Set the required API keys:

```bash
export OPENAI_API_KEY="your-api-key-here"
# Or for Anthropic:
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Step 8: Enable the Assistant (Optional)

The assistant widget is enabled by default. To control it, set `ASSISTANT_ENABLED` in your settings:

```python
WAGTAIL_CONTEXT_SEARCH = {
    # ... other settings ...
    "ASSISTANT_ENABLED": True,  # Widget appears automatically on all pages
    # or
    "ASSISTANT_ENABLED": False,  # Widget is hidden (API still works)
}
```

**Note:** The widget is automatically injected by the middleware. You don't need to add any template tags or edit your templates.

### Alternative: Manual Template Inclusion (Optional)

If you prefer to manually include the widget in your templates instead of using middleware:

1. Remove the middleware from `MIDDLEWARE`
2. Add URLs to your `urls.py`:
   ```python
   path('rag/', include('wagtail_context_search.urls')),
   ```
3. Add the template tag to your base template:
   ```html
   {% load rag_assistant %}
   {% rag_assistant %}
   ```

## Step 9: Index Your Content

Index your existing pages:

```bash
python manage.py rag_index
```

This will index all live pages. For more options, see [USAGE.md](USAGE.md).

## Step 10: Verify Installation

1. Check that the assistant widget appears on your pages
2. Try asking a question
3. Check the health endpoint: `http://your-site.com/rag/health/`

## Troubleshooting

### Widget doesn't appear
- Check that the middleware is added to `MIDDLEWARE` in settings.py
- Verify `ASSISTANT_ENABLED: True` in your configuration
- Check that static files are collected: `python manage.py collectstatic`
- Check browser console for JavaScript errors
- Verify the page has a `</body>` tag (required for automatic injection)

### Backend not available
- Verify the backend package is installed
- Check API keys are set correctly
- For local backends (Ollama, ChromaDB), ensure services are running

### Indexing fails
- Check that pages have content to extract
- Verify vector database is accessible
- Check logs for specific error messages

## Next Steps

- Read [CONFIGURATION.md](CONFIGURATION.md) for advanced configuration
- See [USAGE.md](USAGE.md) for usage examples
- Check [DEVELOPER.md](DEVELOPER.md) to extend the plugin
