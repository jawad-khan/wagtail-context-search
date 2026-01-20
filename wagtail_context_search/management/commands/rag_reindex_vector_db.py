"""
Management command to re-index existing pages into the vector database.

This is useful when the database has indexed pages but the vector DB is empty.
"""

from django.core.management.base import BaseCommand

from wagtail_context_search.core.chunker import Chunker
from wagtail_context_search.core.retrieval import RAGRetrieval
from wagtail_context_search.models import ChunkMetadata, IndexedPage
from wagtail_context_search.settings import get_config
from wagtail_context_search.utils import extract_page_content
from wagtail.models import Page


class Command(BaseCommand):
    help = "Re-index existing pages into the vector database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Re-index all indexed pages",
        )

    def handle(self, *args, **options):
        config = get_config()
        reindex_all = options.get("all", False)

        retrieval = RAGRetrieval(config)
        chunker = Chunker(
            chunk_size=config.get("CHUNK_SIZE", 512),
            chunk_overlap=config.get("CHUNK_OVERLAP", 50),
        )

        if reindex_all:
            indexed_pages = IndexedPage.objects.filter(is_active=True)
        else:
            # Only re-index pages that have chunks but might not be in vector DB
            indexed_pages = IndexedPage.objects.filter(
                is_active=True,
                chunks__isnull=False
            ).distinct()

        total = indexed_pages.count()
        self.stdout.write(f"Re-indexing {total} pages into vector database...")

        indexed = 0
        failed = 0

        for indexed_page in indexed_pages:
            try:
                # Get the actual page
                page = indexed_page.page
                if not page:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ Page object not found for IndexedPage {indexed_page.page_id}")
                    )
                    continue

                self.stdout.write(f"\nProcessing page {page.pk}: {page.title}")

                # Extract content
                content = extract_page_content(page)
                if not content:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ No content found for page {page.pk}: {page.title}")
                    )
                    continue
                
                self.stdout.write(f"  Extracted {len(content)} characters of content")

                # Chunk content
                chunks = chunker.chunk_text(content)
                self.stdout.write(f"  Created {len(chunks)} chunks")

                # Prepare documents
                documents = []
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

                # Add to vector DB
                if documents:
                    try:
                        self.stdout.write(f"  Adding {len(documents)} chunks to vector DB for page {page.pk}...")
                        retrieval.add_documents(documents)
                        indexed += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✓ Successfully indexed page {page.pk}: {page.title} ({len(documents)} chunks)")
                        )
                        if indexed % 10 == 0:
                            self.stdout.write(f"Progress: {indexed}/{total} pages...")
                    except Exception as e:
                        import traceback
                        self.stdout.write(
                            self.style.ERROR(f"  ✗ Failed to add documents to vector DB for page {page.pk}: {str(e)}")
                        )
                        self.stdout.write(traceback.format_exc())
                        failed += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ No chunks for page {page.pk}: {page.title}")
                    )

            except Exception as e:
                failed += 1
                import traceback
                self.stdout.write(
                    self.style.ERROR(f"Failed to re-index page {indexed_page.page_id}: {str(e)}")
                )
                self.stdout.write(traceback.format_exc())

        self.stdout.write(
            self.style.SUCCESS(
                f"Re-indexing complete: {indexed} indexed, {failed} failed"
            )
        )
