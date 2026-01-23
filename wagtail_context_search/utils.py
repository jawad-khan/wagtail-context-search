"""
Utility functions for content extraction and processing.
"""

import html
import re
from typing import Optional

from wagtail.models import Page


def get_page_url(page: Page) -> str:
    """
    Get page URL safely, handling cases where it might not be available.
    
    Args:
        page: Wagtail Page instance
        
    Returns:
        Page URL or empty string if not available
    """
    try:
        if hasattr(page, "get_full_url"):
            url = page.get_full_url()
            if url:
                return url
        # Fallback: try to construct URL from url_path
        if hasattr(page, "url_path"):
            return page.url_path
        # Last resort: return empty string
        return ""
    except Exception:
        return ""


def extract_page_content(page: Page) -> Optional[str]:
    """
    Extract text content from a Wagtail page.

    Args:
        page: Wagtail Page instance

    Returns:
        Extracted text content or None
    """
    content_parts = []

    # Add title
    if page.title:
        content_parts.append(page.title)

    # Extract from streamfield if available
    if hasattr(page, "body") and page.body:
        content_parts.append(extract_streamfield_text(page.body))

    # Extract from rich text fields
    for field in page._meta.get_fields():
        if hasattr(field, "get_internal_type"):
            if field.get_internal_type() == "TextField":
                value = getattr(page, field.name, None)
                if value:
                    content_parts.append(str(value))

    # Join and clean
    text = " ".join(content_parts)
    text = clean_html(text)
    return text.strip() if text.strip() else None


def extract_streamfield_text(streamfield) -> str:
    """Extract text from a StreamField."""
    if not streamfield:
        return ""

    text_parts = []
    for block in streamfield:
        if hasattr(block, "value"):
            value = block.value
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, dict):
                # Extract text from dict values
                for v in value.values():
                    if isinstance(v, str):
                        text_parts.append(v)
        elif isinstance(block, str):
            text_parts.append(block)

    return " ".join(text_parts)


def clean_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode HTML entities
    text = html.unescape(text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()
