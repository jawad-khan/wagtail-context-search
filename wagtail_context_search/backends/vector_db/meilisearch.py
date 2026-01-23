"""
Meilisearch vector database backend implementation.

Note: This backend currently uses Meilisearch's full-text search rather than
native vector similarity. Embeddings are stored on the documents but are not
used in the search query yet. This still satisfies the BaseVectorDB interface
and provides a useful, fast search backend.
"""

from typing import Any, Dict, List, Optional

from wagtail_context_search.backends.vector_db.base import BaseVectorDB


class MeilisearchBackend(BaseVectorDB):
    """Meilisearch backend implementing the BaseVectorDB interface."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Meilisearch backend."""
        super().__init__(config)
        self.url = self.backend_settings.get("url", "http://localhost:7700")
        self.api_key = self.backend_settings.get("api_key")
        self._client = None
        self._index = None

    # --- Internal helpers -------------------------------------------------

    def _get_client(self):
        """Lazy-load Meilisearch client."""
        if self._client is None:
            try:
                import meilisearch  # type: ignore

                if self.api_key:
                    self._client = meilisearch.Client(self.url, self.api_key)
                else:
                    self._client = meilisearch.Client(self.url)
            except ImportError as e:  # pragma: no cover - import error path
                raise ImportError(
                    "meilisearch package is required. Install with: pip install meilisearch"
                ) from e
        return self._client

    def _get_index(self):
        """Get or create the index for this collection."""
        if self._index is None:
            client = self._get_client()
            try:
                self._index = client.get_index(self.collection_name)
                # Ensure searchable attributes are configured
                self._ensure_searchable_attributes(self._index)
            except Exception:
                # Create index if it doesn't exist
                # create_index returns a TaskInfo, so we need to wait for it
                task = client.create_index(
                    self.collection_name, {"primaryKey": "id"}
                )
                # Wait for the task to complete
                # TaskInfo has a task_uid attribute, use client.wait_for_task
                if hasattr(task, 'task_uid'):
                    client.wait_for_task(task.task_uid)
                elif hasattr(client, 'wait_for_task') and hasattr(task, 'uid'):
                    client.wait_for_task(task.uid)
                # Now get the actual index
                self._index = client.get_index(self.collection_name)
                # Configure searchable attributes
                self._ensure_searchable_attributes(self._index)
        return self._index

    def _ensure_searchable_attributes(self, index):
        """Ensure searchable attributes are configured in Meilisearch."""
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Get current settings
            try:
                settings = index.get_searchable_attributes()
                logger.debug(f"Current searchable attributes: {settings}")
            except Exception as e:
                logger.debug(f"Could not get searchable attributes: {str(e)}")
                settings = None
            
            # Meilisearch behavior:
            # - If searchable_attributes is None: searches all fields (default)
            # - If searchable_attributes is [] (empty list): searches NO fields (problem!)
            # - If searchable_attributes is a list: only searches those fields
            needs_update = False
            if settings is None:
                # None means search all fields - this is fine, no update needed
                logger.debug("Searchable attributes is None - Meilisearch will search all fields")
                needs_update = False
            elif isinstance(settings, list):
                if len(settings) == 0:
                    # Empty list means NO fields are searchable - this is the problem!
                    logger.warning("Searchable attributes is empty list - no fields are searchable! Setting to field names.")
                    needs_update = True
                    # Set to actual field names (Meilisearch API requires a list, not None)
                    searchable_attrs = ['text', 'title', 'url', 'page_id', 'page_type', 'chunk_index']
                elif '*' in settings:
                    # '*' is not supported by Meilisearch - replace with actual field names
                    logger.warning("Found '*' in searchable attributes - Meilisearch doesn't support this. Replacing with field names.")
                    needs_update = True
                    searchable_attrs = ['text', 'title', 'url', 'page_id', 'page_type', 'chunk_index']
                elif 'text' not in settings:
                    # 'text' not in the list - add it
                    logger.debug(f"'text' not in searchable attributes {settings}, adding it")
                    needs_update = True
                    searchable_attrs = settings + ['text']
                else:
                    # 'text' is already in the list - no update needed
                    logger.debug(f"Searchable attributes already configured correctly: {settings}")
                    needs_update = False
            
            if needs_update:
                # Update searchable attributes
                # Meilisearch's update_searchable_attributes requires a list
                # To reset to default (search all fields), we need to use reset_searchable_attributes
                if searchable_attrs is None:
                    # Try to reset to default (searches all fields)
                    try:
                        # Check if reset method exists
                        if hasattr(index, 'reset_searchable_attributes'):
                            task = index.reset_searchable_attributes()
                            logger.info("Resetting searchable attributes to default (all fields)")
                        else:
                            # Fallback: set to common fields we know exist in documents
                            # Don't use '*' - Meilisearch doesn't support it
                            searchable_attrs = ['text', 'title', 'url', 'page_id', 'page_type', 'chunk_index']
                            task = index.update_searchable_attributes(searchable_attrs)
                            logger.info(f"Setting searchable attributes to: {searchable_attrs}")
                    except Exception as e2:
                        logger.error(f"Could not reset searchable attributes: {str(e2)}")
                        # Last resort: try setting to common fields
                        try:
                            searchable_attrs = ['text', 'title', 'url']
                            task = index.update_searchable_attributes(searchable_attrs)
                            logger.info(f"Fallback: Setting searchable attributes to: {searchable_attrs}")
                        except Exception as e3:
                            logger.error(f"Could not update searchable attributes: {str(e3)}")
                            return
                else:
                    # If searchable_attrs contains '*', replace it with actual field names
                    if isinstance(searchable_attrs, list) and '*' in searchable_attrs:
                        logger.warning("Found '*' in searchable attributes - Meilisearch doesn't support this. Replacing with actual field names.")
                        searchable_attrs = ['text', 'title', 'url', 'page_id', 'page_type', 'chunk_index']
                    
                    task = index.update_searchable_attributes(searchable_attrs)
                    logger.info(f"Updating searchable attributes to: {searchable_attrs}")
                
                # Wait for the task to complete
                client = self._get_client()
                if hasattr(task, 'task_uid'):
                    client.wait_for_task(task.task_uid)
                elif hasattr(client, 'wait_for_task') and hasattr(task, 'uid'):
                    client.wait_for_task(task.uid)
                logger.info("Searchable attributes update completed")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not configure searchable attributes: {str(e)}")
            # Continue anyway - Meilisearch may search all fields by default

    # --- BaseVectorDB API -------------------------------------------------

    def is_available(self) -> bool:
        """Check if Meilisearch is available."""
        try:
            client = self._get_client()
            # Simple call to verify connectivity
            client.health()
            return True
        except Exception:
            return False

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> None:
        """
        Add documents to Meilisearch.

        Embeddings are stored in an `embedding` field but not used for query yet.
        """
        if not documents:
            return

        index = self._get_index()

        meili_docs: List[Dict[str, Any]] = []
        for i, doc in enumerate(documents):
            meili_doc: Dict[str, Any] = {
                "id": doc["id"],
                "text": doc.get("text", ""),
            }

            # Flatten metadata into top-level fields for filtering / display
            metadata = doc.get("metadata", {}) or {}
            for key, value in metadata.items():
                if value is not None:
                    meili_doc[key] = value

            # Store embedding if provided
            if embeddings and i < len(embeddings):
                meili_doc["embedding"] = embeddings[i]

            meili_docs.append(meili_doc)

        # Ensure searchable attributes are configured before adding documents
        self._ensure_searchable_attributes(index)

        # add_documents returns a TaskInfo, wait for it to complete
        task = index.add_documents(meili_docs)
        client = self._get_client()
        # Wait for the task to complete to ensure documents are indexed
        if hasattr(task, 'task_uid'):
            client.wait_for_task(task.task_uid)
        elif hasattr(client, 'wait_for_task') and hasattr(task, 'uid'):
            client.wait_for_task(task.uid)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using vector similarity.
        
        Since Meilisearch doesn't natively support vector similarity search,
        we implement it by:
        1. Getting all documents (or a large sample)
        2. Computing cosine similarity between query embedding and document embeddings
        3. Returning top_k most similar documents
        """
        import logging
        import math
        logger = logging.getLogger(__name__)
        
        try:
            index = self._get_index()
            
            # Get all documents with their embeddings
            # Note: This is not efficient for large indexes, but Meilisearch doesn't
            # support native vector similarity search
            try:
                # Get documents - we need to get enough to find top_k similar ones
                # For efficiency, we could limit this, but for now get all
                docs_result = index.get_documents({"limit": 10000})  # Get up to 10k docs
                
                if isinstance(docs_result, dict):
                    all_docs = docs_result.get("results", [])
                elif hasattr(docs_result, "results"):
                    all_docs = docs_result.results
                else:
                    all_docs = []
                
                if not all_docs:
                    logger.warning("No documents found in Meilisearch index for vector search")
                    return []
                
                # Compute cosine similarity for each document
                similarities = []
                for doc in all_docs:
                    if isinstance(doc, dict):
                        doc_embedding = doc.get("embedding")
                        doc_id = doc.get("id")
                        doc_text = doc.get("text", "")
                        doc_dict = doc
                    else:
                        doc_embedding = getattr(doc, "embedding", None)
                        doc_id = getattr(doc, "id", None)
                        doc_text = getattr(doc, "text", "")
                        try:
                            doc_dict = dict(doc) if hasattr(doc, "__dict__") else {}
                        except Exception:
                            doc_dict = {}
                    
                    if not doc_embedding or not isinstance(doc_embedding, list):
                        continue
                    
                    # Compute cosine similarity
                    try:
                        # Cosine similarity: dot product / (norm1 * norm2)
                        dot_product = sum(a * b for a, b in zip(query_embedding, doc_embedding))
                        norm1 = math.sqrt(sum(a * a for a in query_embedding))
                        norm2 = math.sqrt(sum(a * a for a in doc_embedding))
                        
                        if norm1 == 0 or norm2 == 0:
                            similarity = 0.0
                        else:
                            similarity = dot_product / (norm1 * norm2)
                        
                        # Extract metadata
                        metadata = {
                            k: v
                            for k, v in doc_dict.items()
                            if k not in {"id", "text", "embedding", "_rankingScore", "_ranking_score"}
                        }
                        
                        similarities.append({
                            "id": str(doc_id) if doc_id else "",
                            "text": doc_text,
                            "metadata": metadata,
                            "score": similarity,
                        })
                    except Exception as e:
                        logger.debug(f"Error computing similarity for doc {doc_id}: {str(e)}")
                        continue
                
                # Sort by similarity (descending) and return top_k
                similarities.sort(key=lambda x: x["score"], reverse=True)
                return similarities[:top_k]
                
            except Exception as e:
                logger.error(f"Error in Meilisearch vector search: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"Error in Meilisearch search: {str(e)}")
            return []

    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from Meilisearch."""
        if not document_ids:
            return

        index = self._get_index()
        # delete_documents returns a TaskInfo, wait for it to complete
        task = index.delete_documents(document_ids)
        client = self._get_client()
        # Wait for the task to complete
        if hasattr(task, 'task_uid'):
            client.wait_for_task(task.task_uid)
        elif hasattr(client, 'wait_for_task') and hasattr(task, 'uid'):
            client.wait_for_task(task.uid)

    def delete_all(self) -> None:
        """Delete all documents from Meilisearch."""
        client = self._get_client()
        try:
            # delete_index returns a TaskInfo, wait for it to complete
            task = client.delete_index(self.collection_name)
            # Wait for the task to complete
            if hasattr(task, 'task_uid'):
                client.wait_for_task(task.task_uid)
            elif hasattr(client, 'wait_for_task') and hasattr(task, 'uid'):
                client.wait_for_task(task.uid)
            self._index = None
        except Exception:
            # Index might not exist yet
            pass

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        try:
            index = self._get_index()
            stats = index.get_stats()
            # Meilisearch returns an IndexStats object, not a dict
            # Access attributes directly or convert to dict
            if hasattr(stats, 'number_of_documents'):
                doc_count = stats.number_of_documents
            elif hasattr(stats, 'numberOfDocuments'):
                doc_count = stats.numberOfDocuments
            elif isinstance(stats, dict):
                doc_count = stats.get("numberOfDocuments", stats.get("number_of_documents", 0))
            else:
                # Try to convert to dict if possible
                try:
                    stats_dict = dict(stats) if hasattr(stats, '__iter__') else {}
                    doc_count = stats_dict.get("numberOfDocuments", stats_dict.get("number_of_documents", 0))
                except Exception:
                    doc_count = 0
            return {"document_count": doc_count}
        except Exception as e:
            # Return 0 but could log the error for debugging
            return {"document_count": 0, "error": str(e)}

    # --- Convenience API used by retrieval -------------------------------

    def search_text(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search by text using Meilisearch full-text search.

        This is used by RAGRetrieval instead of `search()` for Meilisearch.
        """
        if not query_text:
            return []

        try:
            import logging
            logger = logging.getLogger(__name__)
            
            index = self._get_index()
            
            # Check if index has any documents first
            try:
                stats = index.get_stats()
                if hasattr(stats, 'number_of_documents'):
                    doc_count = stats.number_of_documents
                elif hasattr(stats, 'numberOfDocuments'):
                    doc_count = stats.numberOfDocuments
                elif isinstance(stats, dict):
                    doc_count = stats.get('numberOfDocuments', stats.get('number_of_documents', 0))
                else:
                    doc_count = 0
                
                logger.debug(f"Meilisearch index has {doc_count} documents")
                
                if doc_count == 0:
                    logger.warning(f"Meilisearch index '{self.collection_name}' is empty. Run: python manage.py rag_reindex_vector_db --all")
                    return []
                
                # Check and fix searchable attributes if needed
                try:
                    searchable_attrs = index.get_searchable_attributes()
                    logger.debug(f"Current searchable attributes: {searchable_attrs}")
                    if isinstance(searchable_attrs, list) and len(searchable_attrs) == 0:
                        logger.warning("Searchable attributes is empty - fixing now...")
                        self._ensure_searchable_attributes(index)
                        # Re-get index to ensure changes are applied
                        index = self._get_index()
                except Exception as e:
                    logger.warning(f"Could not check searchable attributes: {str(e)}")
            except Exception as e:
                logger.warning(f"Could not check index stats: {str(e)}")

            search_params: Dict[str, Any] = {"limit": top_k}
            
            logger.debug(f"Searching Meilisearch with query: '{query_text}', params: {search_params}")

            # Try to get a sample document to verify structure
            try:
                # Get first document to check structure
                stats = index.get_stats()
                if hasattr(stats, 'number_of_documents'):
                    doc_count = stats.number_of_documents
                elif hasattr(stats, 'numberOfDocuments'):
                    doc_count = stats.numberOfDocuments
                else:
                    doc_count = 0
                
                if doc_count > 0:
                    # Try to get a sample document
                    try:
                        # Use offset=0, limit=1 to get first document
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
                                logger.debug(f"Sample document fields: {list(sample_doc.keys()) if isinstance(sample_doc, dict) else 'N/A'}")
                                if isinstance(sample_doc, dict):
                                    text_content = sample_doc.get("text", "")
                                    logger.debug(f"Sample document 'text' field length: {len(text_content) if text_content else 0}")
                    except Exception as e:
                        logger.debug(f"Could not get sample document: {str(e)}")
            except Exception as e:
                logger.debug(f"Could not check document structure: {str(e)}")

            result = index.search(query_text, search_params)
            
            logger.debug(f"Meilisearch search result type: {type(result)}")
            
            # Handle both dict and object responses from Meilisearch
            if isinstance(result, dict):
                hits = result.get("hits", []) or []
                logger.debug(f"Search result dict keys: {list(result.keys())}")
            elif hasattr(result, "hits"):
                hits = result.hits or []
            elif hasattr(result, "__iter__") and not isinstance(result, str):
                # Result might be iterable (list of hits directly)
                hits = list(result) if result else []
            else:
                hits = []
            
            logger.debug(f"Found {len(hits)} hits for query: {query_text}")
            
            if len(hits) == 0:
                logger.warning(f"No search results for query '{query_text}'. Index may be empty or query doesn't match any documents.")
                # Try a very simple search to see if search works at all
                try:
                    simple_result = index.search("", {"limit": 1})
                    logger.debug(f"Empty query search result: {simple_result}")
                except Exception as e:
                    logger.debug(f"Empty query search failed: {str(e)}")

            documents: List[Dict[str, Any]] = []
            for hit in hits:
                # Handle both dict and object hit structures
                if isinstance(hit, dict):
                    hit_id = hit.get("id")
                    hit_text = hit.get("text", "")
                    hit_score = hit.get("_rankingScore", 0.0)
                    hit_dict = hit
                else:
                    # Object with attributes
                    hit_id = getattr(hit, "id", None)
                    hit_text = getattr(hit, "text", "")
                    hit_score = getattr(hit, "_rankingScore", getattr(hit, "_ranking_score", 0.0))
                    # Convert to dict if possible
                    try:
                        hit_dict = dict(hit) if hasattr(hit, "__dict__") else {}
                    except Exception:
                        hit_dict = {}
                
                # Extract metadata (everything except id, text, embedding, and ranking score)
                metadata = {
                    k: v
                    for k, v in hit_dict.items()
                    if k not in {"id", "text", "embedding", "_rankingScore", "_ranking_score"}
                }
                
                documents.append(
                    {
                        "id": str(hit_id) if hit_id else "",
                        "text": hit_text,
                        "metadata": metadata,
                        "score": float(hit_score),
                    }
                )

            return documents
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Meilisearch search error: {str(e)}")
            return []

{
  "cells": [],
  "metadata": {
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 2
}