# Wagtail Context Search

A powerful RAG (Retrieval-Augmented Generation) based site search plugin for Wagtail CMS. This plugin provides an intelligent assistant that can answer questions about your site's content using AI.

## Features

- 🤖 **AI-Powered Search**: Uses RAG to provide intelligent answers based on your site content
- 🔌 **Pluggable Backends**: Choose your LLM, embedding model, and vector database
- 🔄 **Auto-Indexing**: Automatically indexes pages when published/unpublished
- 💬 **Chat Interface**: Beautiful chat widget that appears on every page
- 📊 **Management Commands**: Easy commands to index, sync, and manage content
- 🎨 **Customizable**: Theme, position, and UI mode options

## Supported Backends

### LLM Providers
- **OpenAI** (GPT-3.5, GPT-4, etc.)
- **Anthropic** (Claude)
- **Ollama** (Local models)

### Embedding Models
- **OpenAI Embeddings**
- **Sentence Transformers** (Local, free)

### Vector Databases
- **ChromaDB** (Local, easy setup)
- **PostgreSQL with pgvector**
- **Qdrant**

## Installation

1. Install the package:
```bash
pip install wagtail-context-search
```

2. Add to your `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... other apps
    'wagtail_context_search',
]
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Include the assistant widget in your base template:
```html
{% load rag_assistant %}
{% rag_assistant %}
```

5. Configure your settings (see [Configuration](docs/CONFIGURATION.md))

6. Index your content:
```bash
python manage.py rag_index
```

## Quick Start

1. **Configure your backends** in `settings.py`:
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

2. **Set environment variables**:
```bash
export OPENAI_API_KEY="your-api-key"
```

3. **Index your pages**:
```bash
python manage.py rag_index
```

4. **The assistant will appear on every page!**

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Configuration Reference](docs/CONFIGURATION.md)
- [Usage Guide](docs/USAGE.md)
- [Developer Guide](docs/DEVELOPER.md)
- [Contributing](docs/CONTRIBUTING.md)

## Management Commands

### Index Pages
```bash
# Index all live pages
python manage.py rag_index

# Index specific page
python manage.py rag_index --page-id=123

# Rebuild entire index
python manage.py rag_index --rebuild
```

### Sync Changes
```bash
# Sync incremental changes
python manage.py rag_sync
```

### Remove Pages
```bash
# Remove specific page
python manage.py rag_remove --page-id=123

# Remove all pages
python manage.py rag_remove --all
```

## Configuration

See [CONFIGURATION.md](docs/CONFIGURATION.md) for detailed configuration options.

## Requirements

- Python 3.10+
- Django 4.2+
- Wagtail 7.0+

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/yourusername/wagtail-context-search/issues)
- Documentation: [Full documentation](docs/)

## Acknowledgments

Built with love for the Wagtail community.
