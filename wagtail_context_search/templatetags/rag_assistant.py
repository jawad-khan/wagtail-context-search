"""
Template tag to include the RAG assistant widget.

Usage in templates:
    {% load rag_assistant %}
    {% rag_assistant %}
"""

from django import template
from django.urls import reverse, NoReverseMatch

from wagtail_context_search.settings import get_config

register = template.Library()


@register.inclusion_tag(
    "wagtail_context_search/assistant_widget.html",
    takes_context=True,
)
def rag_assistant(context):
    """Include the RAG assistant widget."""
    config = get_config()
    
    # Try to get the URL using reverse, fallback to relative URL
    api_url = "/rag/query/"
    try:
        api_url = reverse("wagtail_context_search:query")
        # Make it absolute if we have request context
        request = context.get("request")
        if request:
            api_url = request.build_absolute_uri(api_url)
    except NoReverseMatch:
        # URLs not configured - use relative URL
        request = context.get("request")
        if request:
            api_url = request.build_absolute_uri("/rag/query/")
        else:
            api_url = "/rag/query/"
    except Exception:
        # Any other error - use relative URL
        request = context.get("request")
        if request:
            api_url = request.build_absolute_uri("/rag/query/")
        else:
            api_url = "/rag/query/"
    
    return {
        "config": config,
        "api_url": api_url,
    }
