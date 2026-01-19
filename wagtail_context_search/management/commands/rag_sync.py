"""
Management command to sync incremental changes to the index.

Usage:
    python manage.py rag_sync              # Sync all changes since last run
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from wagtail.models import Page

from wagtail_context_search.core.chunker import Chunker
from wagtail_context_search.core.retrieval import RAGRetrieval
from wagtail_context_search.management.commands.rag_index import Command as IndexCommand
from wagtail_context_search.models import IndexedPage
from wagtail_context_search.settings import get_config


class Command(BaseCommand):
    help = "Sync incremental changes to RAG index"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force sync all pages regardless of modification time",
        )

    def handle(self, *args, **options):
        config = get_config()
        force = options.get("force", False)

        retrieval = RAGRetrieval(config)
        chunker = Chunker(
            chunk_size=config.get("CHUNK_SIZE", 512),
            chunk_overlap=config.get("CHUNK_OVERLAP", 50),
        )

        # Get all live pages
        live_pages = Page.objects.live()
        
        # Filter by page types if configured
        page_types = config.get("PAGE_TYPES", [])
        if page_types:
            live_pages = live_pages.filter(
                content_type__model__in=[pt.lower() for pt in page_types]
            )

        # Get indexed pages
        indexed_pages = {
            ip.page_id: ip
            for ip in IndexedPage.objects.filter(is_active=True)
        }

        to_index = []
        to_update = []
        to_remove = []

        # Find pages that need indexing
        for page in live_pages:
            indexed_page = indexed_pages.get(page.pk)
            
            if not indexed_page:
                # New page, needs indexing
                to_index.append(page)
            elif force or (
                indexed_page.last_modified < (
                    page.last_published_at or page.latest_revision_created_at
                )
            ):
                # Page has been updated
                to_update.append(page)

        # Find pages that should be removed (unpublished)
        for page_id, indexed_page in indexed_pages.items():
            if not Page.objects.filter(pk=page_id, live=True).exists():
                to_remove.append(indexed_page)

        self.stdout.write(f"Found {len(to_index)} new pages to index")
        self.stdout.write(f"Found {len(to_update)} pages to update")
        self.stdout.write(f"Found {len(to_remove)} pages to remove")

        # Index new pages
        index_cmd = IndexCommand()
        for page in to_index:
            try:
                index_cmd.index_page(page, retrieval, chunker, config)
                self.stdout.write(f"Indexed new page: {page.title} (ID: {page.pk})")
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Failed to index page {page.pk}: {str(e)}")
                )

        # Update existing pages
        for page in to_update:
            try:
                index_cmd.index_page(page, retrieval, chunker, config)
                self.stdout.write(f"Updated page: {page.title} (ID: {page.pk})")
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Failed to update page {page.pk}: {str(e)}")
                )

        # Remove unpublished pages
        for indexed_page in to_remove:
            try:
                # Get chunk IDs
                from wagtail_context_search.models import ChunkMetadata
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

                self.stdout.write(
                    f"Removed page: {indexed_page.title} (ID: {indexed_page.page_id})"
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Failed to remove page {indexed_page.page_id}: {str(e)}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Sync complete: {len(to_index)} indexed, "
                f"{len(to_update)} updated, {len(to_remove)} removed"
            )
        )
