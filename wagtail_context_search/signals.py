"""
Wagtail signals for automatic indexing when pages are published/unpublished.
"""

from django.db import transaction
from wagtail.models import Page
from wagtail.signals import page_published, page_unpublished

from wagtail_context_search.core.chunker import Chunker
from wagtail_context_search.core.retrieval import RAGRetrieval
from wagtail_context_search.models import ChunkMetadata, IndexedPage
from wagtail_context_search.settings import get_config
from wagtail_context_search.utils import extract_page_content


def index_page_on_publish(sender, instance, **kwargs):
    """Index a page when it's published."""
    config = get_config()
    
    # Check if this page type should be indexed
    page_types = config.get("PAGE_TYPES", [])
    if page_types and instance.__class__.__name__ not in page_types:
        return

    try:
        with transaction.atomic():
            retrieval = RAGRetrieval(config)
            chunker = Chunker(
                chunk_size=config.get("CHUNK_SIZE", 512),
                chunk_overlap=config.get("CHUNK_OVERLAP", 50),
            )

            # Extract content
            content = extract_page_content(instance)
            if not content:
                return

            # Chunk content
            chunks = chunker.chunk_text(content)

            # Prepare documents
            documents = []
            chunk_metadatas = []
            
            for i, chunk_text in enumerate(chunks):
                chunk_id = f"page_{instance.pk}_chunk_{i}"
                documents.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "page_id": instance.pk,
                        "page_type": instance.__class__.__name__,
                        "title": instance.title,
                        "url": instance.get_full_url() if hasattr(instance, "get_full_url") else "",
                        "chunk_index": i,
                    },
                })
                chunk_metadatas.append({
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "text_preview": chunk_text[:500],
                })

            # Add to vector DB
            retrieval.add_documents(documents)

            # Update or create IndexedPage
            indexed_page, created = IndexedPage.objects.update_or_create(
                page=instance,
                defaults={
                    "page_type": instance.__class__.__name__,
                    "title": instance.title,
                    "url": instance.get_full_url() if hasattr(instance, "get_full_url") else "",
                    "last_modified": instance.last_published_at or instance.latest_revision_created_at,
                    "chunk_count": len(chunks),
                    "is_active": True,
                },
            )

            # Delete old chunks and create new ones
            ChunkMetadata.objects.filter(page=indexed_page).delete()
            for chunk_meta in chunk_metadatas:
                ChunkMetadata.objects.create(
                    page=indexed_page,
                    **chunk_meta,
                )

    except Exception as e:
        # Log error but don't fail the publish
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to index page {instance.pk}: {str(e)}")


def remove_page_on_unpublish(sender, instance, **kwargs):
    """Remove a page from the index when it's unpublished."""
    try:
        config = get_config()
        retrieval = RAGRetrieval(config)

        # Get all chunk IDs for this page
        try:
            indexed_page = IndexedPage.objects.get(page=instance)
            chunk_ids = [
                chunk.chunk_id
                for chunk in ChunkMetadata.objects.filter(page=indexed_page)
            ]

            # Delete from vector DB
            if chunk_ids:
                retrieval.delete_documents(chunk_ids)

            # Mark as inactive
            indexed_page.is_active = False
            indexed_page.save()

            # Optionally delete metadata
            # ChunkMetadata.objects.filter(page=indexed_page).delete()
            # indexed_page.delete()

        except IndexedPage.DoesNotExist:
            pass  # Page wasn't indexed

    except Exception as e:
        # Log error but don't fail the unpublish
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to remove page {instance.pk} from index: {str(e)}")


# Connect signals
page_published.connect(index_page_on_publish, sender=Page)
page_unpublished.connect(remove_page_on_unpublish, sender=Page)
