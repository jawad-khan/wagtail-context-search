"""
Management command to fix Meilisearch searchable attributes.

This command fixes the common issue where Meilisearch has empty searchable_attributes,
which prevents any searches from working.
"""

from django.core.management.base import BaseCommand

from wagtail_context_search.core.retrieval import RAGRetrieval
from wagtail_context_search.settings import get_config


class Command(BaseCommand):
    help = "Fix Meilisearch searchable attributes configuration"

    def handle(self, *args, **options):
        config = get_config()
        
        if config.get("VECTOR_DB_BACKEND") != "meilisearch":
            self.stdout.write(
                self.style.WARNING("This command is only for Meilisearch backend.")
            )
            return
        
        self.stdout.write("Fixing Meilisearch searchable attributes...")
        
        try:
            retrieval = RAGRetrieval(config)
            
            # Get the index - this will trigger _ensure_searchable_attributes
            index = retrieval.vector_db._get_index()
            
            # Check current settings
            try:
                current_attrs = index.get_searchable_attributes()
                self.stdout.write(f"Current searchable attributes: {current_attrs}")
                
                if isinstance(current_attrs, list) and len(current_attrs) == 0:
                    self.stdout.write(
                        self.style.WARNING("⚠ Searchable attributes is empty - fixing now...")
                    )
                elif current_attrs is None:
                    self.stdout.write("Searchable attributes is None (searches all fields) - OK")
                elif isinstance(current_attrs, list) and 'text' in current_attrs:
                    self.stdout.write("Searchable attributes includes 'text' - OK")
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Searchable attributes: {current_attrs} - may need fixing")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Could not get searchable attributes: {str(e)}")
                )
            
            # Force the fix
            retrieval.vector_db._ensure_searchable_attributes(index)
            
            # Check again
            try:
                updated_attrs = index.get_searchable_attributes()
                self.stdout.write(f"Updated searchable attributes: {updated_attrs}")
                
                if isinstance(updated_attrs, list) and len(updated_attrs) == 0:
                    self.stdout.write(
                        self.style.ERROR("❌ Searchable attributes is still empty!")
                    )
                    self.stdout.write("You may need to delete and recreate the index:")
                    self.stdout.write("  1. python manage.py shell")
                    self.stdout.write("  2. from wagtail_context_search.core.retrieval import RAGRetrieval")
                    self.stdout.write("  3. from wagtail_context_search.settings import get_config")
                    self.stdout.write("  4. retrieval = RAGRetrieval(get_config())")
                    self.stdout.write("  5. retrieval.vector_db.delete_all()")
                    self.stdout.write("  6. python manage.py rag_reindex_vector_db --all")
                else:
                    self.stdout.write(
                        self.style.SUCCESS("✓ Searchable attributes fixed!")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Could not verify fix: {str(e)}")
                )
            
            # Check document structure
            self.stdout.write("\nChecking document structure...")
            try:
                # Try to get a sample document
                sample_result = index.get_documents({"limit": 1})
                if sample_result:
                    if isinstance(sample_result, dict):
                        sample_docs = sample_result.get("results", [])
                    elif hasattr(sample_result, "results"):
                        sample_docs = sample_result.results
                    else:
                        sample_docs = []
                    
                    if sample_docs:
                        sample_doc = sample_docs[0]
                        if isinstance(sample_doc, dict):
                            self.stdout.write(f"Sample document fields: {list(sample_doc.keys())}")
                            text_content = sample_doc.get("text", "")
                            if text_content:
                                self.stdout.write(f"Sample 'text' field: {text_content[:100]}...")
                            else:
                                self.stdout.write(
                                    self.style.ERROR("⚠ Sample document 'text' field is EMPTY!")
                                )
                                self.stdout.write("This is why searches return 0 results.")
                                self.stdout.write("You need to reindex documents:")
                                self.stdout.write("  python manage.py rag_reindex_vector_db --all")
                    else:
                        self.stdout.write("Could not get sample document")
                else:
                    self.stdout.write("No documents found in index")
            except Exception as e:
                self.stdout.write(f"Could not check document structure: {str(e)}")
            
            # Test a search
            self.stdout.write("\nTesting search...")
            try:
                results = retrieval.retrieve("test", top_k=1)
                if len(results) > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Search test successful! Found {len(results)} results")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING("⚠ Search test returned 0 results")
                    )
                    self.stdout.write("This might be normal if 'test' doesn't match any documents.")
                    self.stdout.write("Try searching for actual content from your pages.")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Search test failed: {str(e)}")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error: {str(e)}")
            )
            import traceback
            self.stdout.write(traceback.format_exc())
