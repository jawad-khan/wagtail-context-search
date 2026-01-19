"""
Wagtail admin interface for configuration.
"""

from django.contrib import admin

from wagtail_context_search.models import ChunkMetadata, IndexedPage


@admin.register(IndexedPage)
class IndexedPageAdmin(admin.ModelAdmin):
    """Admin interface for IndexedPage model."""

    list_display = ["title", "page_type", "chunk_count", "is_active", "last_indexed"]
    list_filter = ["is_active", "page_type", "last_indexed"]
    search_fields = ["title", "page_type"]
    readonly_fields = ["page", "page_id", "last_indexed"]
    
    fieldsets = (
        ("Page Information", {
            "fields": ("page", "page_id", "page_type", "title", "url"),
        }),
        ("Indexing Information", {
            "fields": ("chunk_count", "is_active", "last_indexed", "last_modified"),
        }),
    )


@admin.register(ChunkMetadata)
class ChunkMetadataAdmin(admin.ModelAdmin):
    """Admin interface for ChunkMetadata model."""

    list_display = ["chunk_id", "page", "chunk_index", "created_at"]
    list_filter = ["created_at", "page"]
    search_fields = ["chunk_id", "text_preview"]
    readonly_fields = ["chunk_id", "created_at"]
    
    fieldsets = (
        ("Chunk Information", {
            "fields": ("chunk_id", "page", "chunk_index"),
        }),
        ("Content", {
            "fields": ("text_preview",),
        }),
        ("Metadata", {
            "fields": ("created_at",),
        }),
    )
