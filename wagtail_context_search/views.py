"""
API views for the RAG assistant.
"""

import json
import logging
from typing import Dict

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from wagtail_context_search.core.generator import RAGGenerator
from wagtail_context_search.core.retrieval import RAGRetrieval
from wagtail_context_search.settings import get_config

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
@csrf_exempt
def query_view(request):
    """
    Handle RAG query requests.

    Expected POST data:
    - query: User's question
    - stream: Optional boolean for streaming response
    """
    config = get_config()

    # Check if assistant is enabled
    if not config.get("ASSISTANT_ENABLED", True):
        return JsonResponse({"error": "Assistant is disabled"}, status=403)

    # Parse request
    try:
        if request.content_type == "application/json":
            data = json.loads(request.body)
        else:
            data = request.POST
    except Exception:
        return JsonResponse({"error": "Invalid request data"}, status=400)

    query = data.get("query", "").strip()
    if not query:
        return JsonResponse({"error": "Query is required"}, status=400)

    stream = data.get("stream", False)

    try:
        # Retrieve relevant documents
        retrieval = RAGRetrieval(config)
        documents = retrieval.retrieve(query)
        
        # Log for debugging
        logger.debug(f"Retrieved {len(documents)} documents for query: {query}")
        if not documents:
            logger.warning(f"No documents found for query: {query}. Vector DB may be empty.")

        # Generate answer
        try:
            generator = RAGGenerator(config)
            # Check if LLM is available
            if not generator.llm.is_available():
                return JsonResponse({
                    "error": f"LLM backend '{config.get('LLM_BACKEND', 'openai')}' is not available. Please check your configuration and ensure the service is running.",
                    "answer": None,
                    "sources": [],
                }, status=503)
        except Exception as e:
            logger.exception("Failed to initialize LLM generator")
            return JsonResponse({
                "error": f"Failed to initialize LLM: {str(e)}. Please check your LLM backend configuration.",
                "answer": None,
                "sources": [],
            }, status=500)

        if stream:
            # Streaming response
            def generate():
                yield '{"type":"start"}\n'
                answer_parts = []
                for chunk in generator.stream_answer(query, documents):
                    answer_parts.append(chunk)
                    yield json.dumps({"type": "chunk", "content": chunk}) + "\n"
                
                # Send sources at the end
                sources = []
                for doc in documents:
                    metadata = doc.get("metadata", {})
                    sources.append({
                        "title": metadata.get("title", "Untitled"),
                        "url": metadata.get("url", ""),
                        "score": doc.get("score", 0.0),
                    })
                yield json.dumps({"type": "sources", "sources": sources}) + "\n"
                yield '{"type":"end"}\n'

            response = StreamingHttpResponse(
                generate(),
                content_type="application/x-ndjson",
            )
            return response
        else:
            # Non-streaming response
            result = generator.generate_answer(query, documents)
            return JsonResponse(result)

    except Exception as e:
        logger.exception("Error processing RAG query")
        return JsonResponse(
            {"error": f"Error processing query: {str(e)}"},
            status=500,
        )


@require_http_methods(["GET"])
def health_view(request):
    """Health check endpoint."""
    config = get_config()
    
    try:
        # Check if backends are available
        retrieval = RAGRetrieval(config)
        generator = RAGGenerator(config)
        
        embedder_available = retrieval.embedder.is_available()
        vector_db_available = retrieval.vector_db.is_available()
        llm_available = generator.llm.is_available()
        
        # Check vector DB stats
        vector_db_stats = {}
        indexed_count = 0
        try:
            vector_db_stats = retrieval.vector_db.get_stats()
            indexed_count = vector_db_stats.get("document_count", 0)
        except Exception:
            pass
        
        # Check database for indexed pages
        try:
            from wagtail_context_search.models import IndexedPage
            db_indexed_count = IndexedPage.objects.filter(is_active=True).count()
        except Exception:
            db_indexed_count = 0
        
        status = {
            "status": "ok" if all([embedder_available, vector_db_available, llm_available]) else "degraded",
            "embedder": "available" if embedder_available else "unavailable",
            "vector_db": "available" if vector_db_available else "unavailable",
            "llm": "available" if llm_available else "unavailable",
            "indexed_documents": indexed_count,
            "db_indexed_pages": db_indexed_count,
        }
        
        status_code = 200 if status["status"] == "ok" else 503
        return JsonResponse(status, status=status_code)
    except Exception as e:
        return JsonResponse(
            {"status": "error", "error": str(e)},
            status=500,
        )
