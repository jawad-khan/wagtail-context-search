"""
Management command to debug vector database issues.
"""

from django.core.management.base import BaseCommand

from wagtail_context_search.core.retrieval import RAGRetrieval
from wagtail_context_search.models import ChunkMetadata, IndexedPage
from wagtail_context_search.settings import get_config


class Command(BaseCommand):
    help = "Debug vector database and indexing status"

    def handle(self, *args, **options):
        from django.conf import settings
        
        config = get_config()
        
        self.stdout.write("=== Wagtail Context Search Debug Info ===\n")
        
        # Configuration check
        self.stdout.write("Configuration Status:")
        user_config = getattr(settings, "WAGTAIL_CONTEXT_SEARCH", {})
        self.stdout.write(f"  User config present: {'✓ Yes' if user_config else '✗ No (using defaults)'}")
        self.stdout.write(f"  LLM Backend: {config.get('LLM_BACKEND')}")
        self.stdout.write(f"  Embedder Backend: {config.get('EMBEDDER_BACKEND')}")
        self.stdout.write(f"  Vector DB Backend: {config.get('VECTOR_DB_BACKEND')}")
        
        # Check API keys (masked)
        backend_settings = config.get("BACKEND_SETTINGS", {})
        self.stdout.write("\n  Backend Settings:")
        for backend_name, backend_config in backend_settings.items():
            if isinstance(backend_config, dict):
                api_key = backend_config.get("api_key")
                if api_key:
                    masked = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
                    self.stdout.write(f"    {backend_name}.api_key: {masked} ✓")
                else:
                    self.stdout.write(self.style.WARNING(f"    {backend_name}.api_key: None ✗"))
        
        self.stdout.write("\nBackend Status:")
        self.stdout.write("Backend Status:")
        try:
            retrieval = RAGRetrieval(config)
            embedder_available = retrieval.embedder.is_available()
            vector_db_available = retrieval.vector_db.is_available()
            
            self.stdout.write(f"  Embedder: {'✓ Available' if embedder_available else '✗ Unavailable'}")
            self.stdout.write(f"  Vector DB: {'✓ Available' if vector_db_available else '✗ Unavailable'}")
            
            if embedder_available:
                try:
                    dimension = retrieval.embedder.get_dimension()
                    self.stdout.write(f"  Embedding dimension: {dimension}")
                except Exception as e:
                    self.stdout.write(f"  Error getting dimension: {str(e)}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error initializing backends: {str(e)}"))
        
        self.stdout.write("\nDatabase Status:")
        try:
            indexed_count = IndexedPage.objects.filter(is_active=True).count()
            total_chunks = ChunkMetadata.objects.count()
            
            self.stdout.write(f"  Indexed pages: {indexed_count}")
            self.stdout.write(f"  Total chunks: {total_chunks}")
            
            # Show sample pages
            if indexed_count > 0:
                self.stdout.write("\n  Sample indexed pages:")
                for page in IndexedPage.objects.filter(is_active=True)[:5]:
                    chunk_count = ChunkMetadata.objects.filter(page=page).count()
                    self.stdout.write(f"    - {page.title} (ID: {page.page_id}, Chunks: {chunk_count})")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error checking database: {str(e)}"))
        
        self.stdout.write("\nVector Database Status:")
        try:
            retrieval = RAGRetrieval(config)
            
            # Check if using ChromaDB and if it's persistent
            if hasattr(retrieval.vector_db, 'persist_directory'):
                persist_dir = retrieval.vector_db.persist_directory
                if persist_dir:
                    self.stdout.write(f"  ChromaDB persistence: {persist_dir}")
                else:
                    self.stdout.write(self.style.WARNING("  ⚠ ChromaDB is in-memory (data lost on restart)"))
                    self.stdout.write("  Configure 'persist_directory' in BACKEND_SETTINGS to persist data")
            
            stats = retrieval.vector_db.get_stats()
            vector_count = stats.get("document_count", 0)
            self.stdout.write(f"  Documents in vector DB: {vector_count}")
            
            # Try to directly query ChromaDB if available
            if hasattr(retrieval.vector_db, '_get_client') and hasattr(retrieval.vector_db, 'persist_directory'):
                # This is ChromaDB
                try:
                    client = retrieval.vector_db._get_client()
                    collections = client.list_collections()
                    self.stdout.write(f"  ChromaDB collections: {[c.name for c in collections]}")
                    for coll in collections:
                        if coll.name == retrieval.vector_db.collection_name:
                            count = coll.count()
                            self.stdout.write(f"    Collection '{coll.name}': {count} documents")
                except Exception as e:
                    self.stdout.write(f"  Could not list collections: {str(e)}")
            elif hasattr(retrieval.vector_db, '_get_index'):
                # This is Meilisearch
                try:
                    index = retrieval.vector_db._get_index()
                    index_stats = index.get_stats()
                    self.stdout.write(f"  Meilisearch index: {retrieval.vector_db.collection_name}")
                    # Handle IndexStats object (not a dict)
                    if hasattr(index_stats, 'number_of_documents'):
                        doc_count = index_stats.number_of_documents
                    elif hasattr(index_stats, 'numberOfDocuments'):
                        doc_count = index_stats.numberOfDocuments
                    elif isinstance(index_stats, dict):
                        doc_count = index_stats.get('numberOfDocuments', index_stats.get('number_of_documents', 0))
                    else:
                        doc_count = 0
                    self.stdout.write(f"    Documents: {doc_count}")
                    
                    # Check searchable attributes
                    try:
                        searchable_attrs = index.get_searchable_attributes()
                        if searchable_attrs is None:
                            self.stdout.write(f"    Searchable attributes: All fields (default)")
                        elif isinstance(searchable_attrs, list) and len(searchable_attrs) == 0:
                            self.stdout.write(self.style.WARNING(f"    ⚠ Searchable attributes: EMPTY (no fields searchable!)"))
                            self.stdout.write(self.style.WARNING(f"    This is why searches return 0 results. Run: python manage.py rag_reindex_vector_db --all"))
                        else:
                            self.stdout.write(f"    Searchable attributes: {searchable_attrs}")
                    except Exception as e:
                        self.stdout.write(f"    Could not get searchable attributes: {str(e)}")
                except Exception as e:
                    self.stdout.write(f"  Could not get index stats: {str(e)}")
            
            # Try a test search
            if vector_count > 0:
                self.stdout.write("\n  Testing search...")
                try:
                    test_query = "test"
                    results = retrieval.retrieve(test_query, top_k=1)
                    self.stdout.write(f"    Test query returned {len(results)} results")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"    Search test failed: {str(e)}"))
            else:
                self.stdout.write(self.style.WARNING("  ⚠ Vector database is empty!"))
                self.stdout.write("  Run: python manage.py rag_reindex_vector_db --all")
        except Exception as e:
            import traceback
            self.stdout.write(self.style.ERROR(f"  Error checking vector DB: {str(e)}"))
            self.stdout.write(traceback.format_exc())
        
        self.stdout.write("\n=== End Debug Info ===")
