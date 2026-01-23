"""
Template context processor for Wagtail Context Search.

This makes the assistant widget available globally without needing to add
the template tag to base.html.
"""

from wagtail_context_search.settings import get_config


def rag_assistant_context(request):
    """
    Template context processor that adds RAG assistant configuration.
    
    Add this to your TEMPLATES context_processors in settings.py:
    'wagtail_context_search.context_processors.rag_assistant_context',
    """
    config = get_config()
    
    # Only add context if assistant is enabled
    if not config.get("ASSISTANT_ENABLED", True):
        return {}
    
    # Build API URL
    api_url = "/rag/query/"
    try:
        from django.urls import reverse
        api_url = reverse("wagtail_context_search:query")
        api_url = request.build_absolute_uri(api_url)
    except Exception:
        api_url = request.build_absolute_uri("/rag/query/")
    
    return {
        "rag_assistant_enabled": True,
        "rag_assistant_config": {
            "api_url": api_url,
            "mode": config.get("ASSISTANT_UI_MODE", "both"),
            "position": config.get("ASSISTANT_POSITION", "bottom-right"),
            "theme": config.get("ASSISTANT_THEME", "light"),
        },
    }
