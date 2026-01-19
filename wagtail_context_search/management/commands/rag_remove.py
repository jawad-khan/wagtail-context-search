"""
Management command to remove pages from the RAG index.

Usage:
    python manage.py rag_remove --page-id=123      # Remove specific page
    python manage.py rag_remove --all              # Remove all pages
"""

from django.core.management.base import BaseCommand, CommandError

from wagtail_context_search.core.retrieval import RAGRetrieval
from wagtail_context_search.models import ChunkMetadata, IndexedPage
from wagtail_context_search.settings import get_config


class Command(BaseCommand):
    help = "Remove pages from RAG index"

    def add_arguments(self, parser):
        parser.add_argument(
            "--page-id",
            type=int,
            help="Remove a specific page by ID",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Remove all pages from index",
        )

    def handle(self, *args, **options):
        config = get_config()
        page_id = options.get("page_id")
        remove_all = options.get("all", False)

        retrieval = RAGRetrieval(config)

        if remove_all:
            # Remove all
            self.stdout.write("Removing all pages from index...")
            
            # Get all chunk IDs
            chunk_ids = [
                chunk.chunk_id
                for chunk in ChunkMetadata.objects.all()
            ]

            # Delete from vector DB
            if chunk_ids:
                retrieval.delete_documents(chunk_ids)

            # Mark all as inactive
            IndexedPage.objects.all().update(is_active=False)

            # Optionally delete metadata
            # ChunkMetadata.objects.all().delete()
            # IndexedPage.objects.all().delete()

            self.stdout.write(self.style.SUCCESS("Removed all pages from index"))
        elif page_id:
            # Remove specific page
            try:
                indexed_page = IndexedPage.objects.get(page__pk=page_id)
                
                # Get chunk IDs
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
                    self.style.SUCCESS(f"Removed page {page_id} from index")
                )
            except IndexedPage.DoesNotExist:
                raise CommandError(f"Page {page_id} is not in the index")
        else:
            raise CommandError("Must specify --page-id or --all")
