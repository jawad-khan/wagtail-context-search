# Developer Guide

Guide for developers who want to extend or contribute to Wagtail Context Search.

## Architecture Overview

The plugin follows a modular architecture with pluggable backends:

```
┌─────────────────┐
│  Frontend UI    │
└────────┬────────┘
         │
┌────────▼────────┐
│   API Views     │
└────────┬────────┘
         │
┌────────▼────────┐
│  RAG Pipeline   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────┐
│Retrieval│ │Generation│
└───┬───┘ └──┬──────┘
    │        │
┌───▼───┐ ┌──▼──────┐
│Embedder│ │   LLM   │
└───┬───┘ └──┬──────┘
    │        │
┌───▼────────▼───┐
│  Vector DB     │
└────────────────┘
```

## Adding a New LLM Backend

1. Create a new file in `wagtail_context_search/backends/llm/`:

```python
from wagtail_context_search.backends.llm.base import BaseLLMBackend

class MyLLMBackend(BaseLLMBackend):
    def __init__(self, config):
        super().__init__(config)
        # Initialize your backend
    
    def is_available(self) -> bool:
        # Check if backend is available
        return True
    
    def generate(self, prompt, system_prompt=None, **kwargs):
        # Implement generation logic
        return "Generated response"
```

2. Register it in `wagtail_context_search/backends/llm/__init__.py`:

```python
from .my_llm import MyLLMBackend

LLM_BACKENDS = {
    # ... existing backends
    "my_llm": MyLLMBackend,
}
```

## Adding a New Embedder Backend

1. Create a new file in `wagtail_context_search/backends/embedder/`:

```python
from wagtail_context_search.backends.embedder.base import BaseEmbedder

class MyEmbedder(BaseEmbedder):
    def __init__(self, config):
        super().__init__(config)
        # Initialize your embedder
    
    def is_available(self) -> bool:
        return True
    
    def get_dimension(self) -> int:
        return 384  # Your embedding dimension
    
    def embed(self, text):
        # Generate embedding
        return [0.1] * self.get_dimension()
    
    def embed_batch(self, texts):
        return [self.embed(text) for text in texts]
```

2. Register it in `wagtail_context_search/backends/embedder/__init__.py`

## Adding a New Vector Database Backend

1. Create a new file in `wagtail_context_search/backends/vector_db/`:

```python
from wagtail_context_search.backends.vector_db.base import BaseVectorDB

class MyVectorDB(BaseVectorDB):
    def __init__(self, config):
        super().__init__(config)
        # Initialize your vector DB
    
    def is_available(self) -> bool:
        return True
    
    def add_documents(self, documents, embeddings):
        # Add documents to your vector DB
        pass
    
    def search(self, query_embedding, top_k=5, filter_dict=None):
        # Search and return documents
        return []
    
    def delete_documents(self, document_ids):
        # Delete documents
        pass
    
    def delete_all(self):
        # Delete all documents
        pass
```

2. Register it in `wagtail_context_search/backends/vector_db/__init__.py`

## Custom Chunking Strategy

Override the chunker:

```python
from wagtail_context_search.core.chunker import Chunker

class MyChunker(Chunker):
    def chunk_text(self, text):
        # Custom chunking logic
        return super().chunk_text(text)
```

## Custom Prompt Templates

Create custom prompt templates:

```python
from wagtail_context_search.core.prompt_templates import PromptTemplate

class MyPromptTemplate(PromptTemplate):
    DEFAULT_SYSTEM_PROMPT = "Your custom system prompt"
    
    def format_context(self, documents):
        # Custom context formatting
        return super().format_context(documents)
```

## Extending Content Extraction

Customize how content is extracted from pages:

```python
from wagtail_context_search.utils import extract_page_content

def my_extract_content(page):
    # Custom extraction logic
    content = extract_page_content(page)
    # Add custom processing
    return content
```

Then use in signals or management commands.

## Testing

### Running Tests

```bash
pytest
```

### Writing Tests

Tests should be in the `tests/` directory. Follow the existing test structure:

```python
from django.test import TestCase
from wagtail_context_search.core.chunker import Chunker

class MyTest(TestCase):
    def test_something(self):
        chunker = Chunker()
        result = chunker.chunk_text("test")
        self.assertEqual(len(result), 1)
```

## Code Style

- Follow PEP 8
- Use type hints where possible
- Write docstrings for public functions
- Keep functions focused and small

## Debugging

### Enable Logging

Add to `settings.py`:

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'wagtail_context_search': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Common Issues

1. **Backend not found**: Check registration in `__init__.py`
2. **Import errors**: Ensure dependencies are installed
3. **Vector DB errors**: Check connection settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## API Reference

### Core Classes

- `RAGRetrieval`: Handles document retrieval
- `RAGGenerator`: Generates answers using LLM
- `Chunker`: Splits text into chunks
- `PromptTemplate`: Manages prompt formatting

### Backend Interfaces

- `BaseLLMBackend`: Abstract LLM backend
- `BaseEmbedder`: Abstract embedding backend
- `BaseVectorDB`: Abstract vector database backend

See source code for detailed API documentation.
