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


@csrf_exempt
@require_http_methods(["POST"])
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

        # Generate answer
        generator = RAGGenerator(config)

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
        
        status = {
            "status": "ok" if all([embedder_available, vector_db_available, llm_available]) else "degraded",
            "embedder": "available" if embedder_available else "unavailable",
            "vector_db": "available" if vector_db_available else "unavailable",
            "llm": "available" if llm_available else "unavailable",
        }
        
        status_code = 200 if status["status"] == "ok" else 503
        return JsonResponse(status, status=status_code)
    except Exception as e:
        return JsonResponse(
            {"status": "error", "error": str(e)},
            status=500,
        )
