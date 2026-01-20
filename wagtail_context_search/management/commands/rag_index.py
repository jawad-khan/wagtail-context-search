"""
Management command to index pages for RAG.

Usage:
    python manage.py rag_index                    # Index all live pages
    python manage.py rag_index --page-id=123      # Index specific page
    python manage.py rag_index --rebuild          # Rebuild entire index
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.models import Page

from wagtail_context_search.core.chunker import Chunker
from wagtail_context_search.core.retrieval import RAGRetrieval
from wagtail_context_search.models import ChunkMetadata, IndexedPage
from wagtail_context_search.settings import get_config
from wagtail_context_search.utils import extract_page_content


class Command(BaseCommand):
    help = "Index pages for RAG search"

    def add_arguments(self, parser):
        parser.add_argument(
            "--page-id",
            type=int,
            help="Index a specific page by ID",
        )
        parser.add_argument(
            "--rebuild",
            action="store_true",
            help="Rebuild the entire index (delete all and re-index)",
        )
        parser.add_argument(
            "--page-type",
            type=str,
            help="Only index pages of this type",
        )

    def handle(self, *args, **options):
        config = get_config()
        page_id = options.get("page_id")
        rebuild = options.get("rebuild", False)
        page_type = options.get("page_type")

        retrieval = RAGRetrieval(config)
        chunker = Chunker(
            chunk_size=config.get("CHUNK_SIZE", 512),
            chunk_overlap=config.get("CHUNK_OVERLAP", 50),
        )

        if rebuild:
            self.stdout.write("Rebuilding index...")
            retrieval.vector_db.delete_all()
            IndexedPage.objects.all().update(is_active=False)
            ChunkMetadata.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared existing index"))

        if page_id:
            # Index specific page
            try:
                page = Page.objects.get(pk=page_id)
                self.index_page(page, retrieval, chunker, config)
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully indexed page {page_id}")
                )
            except Page.DoesNotExist:
                raise CommandError(f"Page with ID {page_id} does not exist")
        else:
            # Index all live pages
            pages = Page.objects.live()
            
            if page_type:
                pages = pages.filter(content_type__model=page_type.lower())
            
            # Filter by page types if configured
            page_types = config.get("PAGE_TYPES", [])
            if page_types:
                pages = pages.filter(content_type__model__in=[pt.lower() for pt in page_types])

            total = pages.count()
            self.stdout.write(f"Indexing {total} pages...")

            indexed = 0
            failed = 0

            for page in pages:
                try:
                    self.index_page(page, retrieval, chunker, config)
                    indexed += 1
                    if indexed % 10 == 0:
                        self.stdout.write(f"Indexed {indexed}/{total} pages...")
                except Exception as e:
                    failed += 1
                    self.stdout.write(
                        self.style.WARNING(f"Failed to index page {page.pk}: {str(e)}")
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Indexing complete: {indexed} indexed, {failed} failed"
                )
            )

    def index_page(self, page, retrieval, chunker, config):
        """Index a single page."""
        # Check if this page type should be indexed
        page_types = config.get("PAGE_TYPES", [])
        if page_types and page.__class__.__name__ not in page_types:
            return

        with transaction.atomic():
            # Extract content
            content = extract_page_content(page)
            if not content:
                return

            # Chunk content
            chunks = chunker.chunk_text(content)

            # Prepare documents
            documents = []
            chunk_metadatas = []

            for i, chunk_text in enumerate(chunks):
                chunk_id = f"page_{page.pk}_chunk_{i}"
                documents.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "page_id": page.pk,
                        "page_type": page.__class__.__name__,
                        "title": page.title,
                        "url": page.get_full_url() if hasattr(page, "get_full_url") else "",
                        "chunk_index": i,
                    },
                })
                chunk_metadatas.append({
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "text_preview": chunk_text[:500],
                })

            # Add to vector DB
            try:
                retrieval.add_documents(documents)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to add documents to vector DB for page {page.pk}: {str(e)}")
                )
                raise

            # Update or create IndexedPage
            indexed_page, created = IndexedPage.objects.update_or_create(
                page=page,
                defaults={
                    "page_type": page.__class__.__name__,
                    "title": page.title,
                    "url": page.get_full_url() if hasattr(page, "get_full_url") else "",
                    "last_modified": page.last_published_at or page.latest_revision_created_at,
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
