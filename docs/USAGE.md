# Usage Guide

How to use Wagtail Context Search in your Wagtail site.

## Basic Usage

Once installed and configured (with the middleware added), the assistant widget will automatically appear on every page of your site (if `ASSISTANT_ENABLED: True` in settings).

**No template changes needed!** The middleware automatically injects the widget into all HTML pages.

### Asking Questions

1. Click the assistant button (bottom-right corner by default)
2. Type your question in the input field
3. Press Enter or click Send
4. The assistant will provide an answer based on your site's content

### Viewing Sources

Answers include links to the source pages. Click on source links to view the original content.

## Management Commands

### Indexing Pages

#### Index All Live Pages

```bash
python manage.py rag_index
```

This indexes all published pages on your site.

#### Index Specific Page

```bash
python manage.py rag_index --page-id=123
```

#### Rebuild Entire Index

```bash
python manage.py rag_index --rebuild
```

This clears the existing index and rebuilds it from scratch.

#### Index Specific Page Type

```bash
python manage.py rag_index --page-type=blogpage
```

### Syncing Changes

The plugin automatically indexes pages when they're published and removes them when unpublished. However, you can manually sync changes:

```bash
python manage.py rag_sync
```

This will:
- Index new pages
- Update modified pages
- Remove unpublished pages

Force sync all pages:

```bash
python manage.py rag_sync --force
```

### Removing Pages

#### Remove Specific Page

```bash
python manage.py rag_remove --page-id=123
```

#### Remove All Pages

```bash
python manage.py rag_remove --all
```

## API Usage

### Query Endpoint

Query the assistant programmatically:

```python
import requests

response = requests.post(
    'http://your-site.com/rag/query/',
    json={
        'query': 'What is this site about?',
        'stream': False,
    },
)

data = response.json()
print(data['answer'])
print(data['sources'])
```

### Streaming Responses

Get streaming responses:

```python
import requests
import json

response = requests.post(
    'http://your-site.com/rag/query/',
    json={
        'query': 'Tell me about your services',
        'stream': True,
    },
    stream=True,
)

for line in response.iter_lines():
    if line:
        data = json.loads(line)
        if data['type'] == 'chunk':
            print(data['content'], end='', flush=True)
```

### Health Check

Check if the assistant is working:

```bash
curl http://your-site.com/rag/health/
```

Response:
```json
{
    "status": "ok",
    "embedder": "available",
    "vector_db": "available",
    "llm": "available"
}
```

## Customization

### Widget Position

Change position in settings:

```python
WAGTAIL_CONTEXT_SEARCH = {
    "ASSISTANT_POSITION": "bottom-left",  # or "bottom-right"
}
```

### Theme

Switch between light and dark themes:

```python
WAGTAIL_CONTEXT_SEARCH = {
    "ASSISTANT_THEME": "dark",  # or "light"
}
```

### UI Mode

Choose between chat, search, or both:

```python
WAGTAIL_CONTEXT_SEARCH = {
    "ASSISTANT_UI_MODE": "chat",  # or "search", "both"
}
```

### Custom Styling

Override CSS by adding your own stylesheet after the plugin's CSS:

```html
<link rel="stylesheet" href="{% static 'wagtail_context_search/css/assistant.css' %}">
<link rel="stylesheet" href="{% static 'myapp/css/custom-assistant.css' %}">
```

## Best Practices

### Regular Indexing

Set up a cron job or scheduled task to regularly sync changes:

```bash
# Run every hour
0 * * * * cd /path/to/project && python manage.py rag_sync
```

### Monitoring

Check the health endpoint regularly to ensure all backends are available.

### Content Quality

- Ensure pages have meaningful text content
- Use descriptive titles and headings
- Keep content up to date

### Performance

- For large sites, consider using a persistent vector database (not in-memory)
- Use batch indexing for better performance
- Monitor vector database size

## Troubleshooting

### Assistant Not Responding

1. Check health endpoint: `/rag/health/`
2. Verify API keys are set
3. Check browser console for errors
4. Verify pages are indexed: Check admin panel

### Poor Answers

1. Ensure pages have sufficient content
2. Try increasing `TOP_K` to retrieve more context
3. Adjust `CHUNK_SIZE` for better chunking
4. Check that relevant pages are indexed

### Indexing Issues

1. Check that pages have extractable content
2. Verify vector database is accessible
3. Check logs for specific errors
4. Try rebuilding index: `python manage.py rag_index --rebuild`

## Advanced Usage

### Custom Prompt Templates

Create custom prompts in settings:

```python
WAGTAIL_CONTEXT_SEARCH = {
    "PROMPT_TEMPLATE": """You are a helpful assistant for {site_name}.

Context:
{context}

Question: {question}

Provide a detailed answer:""",
}
```

### Filtering Page Types

Only index specific page types:

```python
WAGTAIL_CONTEXT_SEARCH = {
    "PAGE_TYPES": [
        "BlogPage",
        "ArticlePage",
    ],
}
```

### Programmatic Indexing

Index pages programmatically:

```python
from wagtail_context_search.core.retrieval import RAGRetrieval
from wagtail_context_search.core.chunker import Chunker
from wagtail_context_search.settings import get_config
from wagtail_context_search.utils import extract_page_content

config = get_config()
retrieval = RAGRetrieval(config)
chunker = Chunker(
    chunk_size=config.get("CHUNK_SIZE", 512),
    chunk_overlap=config.get("CHUNK_OVERLAP", 50),
)

# Get page
page = Page.objects.get(pk=123)

# Extract and chunk
content = extract_page_content(page)
chunks = chunker.chunk_text(content)

# Prepare documents
documents = [{
    "id": f"page_{page.pk}_chunk_{i}",
    "text": chunk,
    "metadata": {
        "page_id": page.pk,
        "title": page.title,
        "url": page.get_full_url(),
    },
} for i, chunk in enumerate(chunks)]

# Index
retrieval.add_documents(documents)
```

## Examples

### Example: FAQ Assistant

Configure to answer frequently asked questions:

```python
WAGTAIL_CONTEXT_SEARCH = {
    "PAGE_TYPES": ["FAQPage"],
    "PROMPT_TEMPLATE": """You are answering frequently asked questions.

Context from FAQ pages:
{context}

Question: {question}

Provide a clear, concise answer:""",
}
```

### Example: Documentation Search

For documentation sites:

```python
WAGTAIL_CONTEXT_SEARCH = {
    "PAGE_TYPES": ["DocumentationPage"],
    "TOP_K": 10,  # Retrieve more context for docs
    "CHUNK_SIZE": 1024,  # Larger chunks for technical content
}
```
