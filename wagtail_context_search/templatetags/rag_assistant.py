"""
Template tag to include the RAG assistant widget.

Usage in templates:
    {% load rag_assistant %}
    {% rag_assistant %}
"""

from django import template
from wagtail_context_search.settings import get_config

register = template.Library()


@register.inclusion_tag(
    "wagtail_context_search/assistant_widget.html",
    takes_context=True,
)
def rag_assistant(context):
    """Include the RAG assistant widget."""
    config = get_config()
    return {
        "config": config,
    }
