"""
Models for storing metadata about indexed pages and chunks.
"""

from django.db import models
from django.utils import timezone
from wagtail.models import Page


class IndexedPage(models.Model):
    """Tracks which pages have been indexed and their metadata."""

    page = models.OneToOneField(
        Page,
        on_delete=models.CASCADE,
        related_name="rag_index",
        primary_key=True,
    )
    page_id = models.PositiveIntegerField(db_index=True)
    page_type = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    url = models.URLField()
    last_indexed = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField()
    chunk_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "wagtail_context_search_indexed_page"
        indexes = [
            models.Index(fields=["is_active", "last_modified"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.page_id})"


class ChunkMetadata(models.Model):
    """Metadata for individual text chunks."""

    chunk_id = models.CharField(max_length=255, unique=True, db_index=True)
    page = models.ForeignKey(
        IndexedPage,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_index = models.PositiveIntegerField()
    text_preview = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wagtail_context_search_chunk_metadata"
        indexes = [
            models.Index(fields=["page", "chunk_index"]),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.page.title}"
