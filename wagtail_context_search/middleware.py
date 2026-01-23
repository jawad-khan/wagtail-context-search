"""
Middleware to automatically inject the RAG assistant widget into HTML responses
and handle URL routing for the RAG API endpoints.

This allows the widget to appear on all pages without editing base.html,
and the API endpoints to work without adding URLs to urls.py.
"""

from django.http import JsonResponse, StreamingHttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve, Resolver404
from wagtail_context_search.settings import get_config
from wagtail_context_search import views


class RAGAssistantMiddleware(MiddlewareMixin):
    """
    Middleware that injects the RAG assistant widget into HTML responses.
    
    Add this to your MIDDLEWARE in settings.py:
    'wagtail_context_search.middleware.RAGAssistantMiddleware',
    """
    
    def process_request(self, request):
        """
        Handle RAG API requests if URLs aren't configured.
        This allows the API to work without adding URLs to urls.py.
        """
        path = request.path
        
        # Only handle /rag/ paths
        if not path.startswith('/rag/'):
            return None
        
        # Try to resolve the URL normally first
        try:
            resolve(path)
            # URL is already configured, let Django handle it
            return None
        except Resolver404:
            # URL not configured, handle it here
            pass
        
        # Handle /rag/query/ endpoint
        if path == '/rag/query/' or path.startswith('/rag/query'):
            return views.query_view(request)
        
        # Handle /rag/health/ endpoint
        if path == '/rag/health/' or path.startswith('/rag/health'):
            return views.health_view(request)
        
        # Unknown /rag/ path
        return JsonResponse({"error": "Not found"}, status=404)
    
    def process_response(self, request, response):
        """Inject the assistant widget script into HTML responses."""
        # Only process HTML responses
        content_type = response.get('Content-Type', '')
        if not content_type.startswith('text/html'):
            return response
        
        # Check if assistant is enabled
        config = get_config()
        if not config.get("ASSISTANT_ENABLED", True):
            return response
        
        # Skip admin and API endpoints
        path = request.path
        if path.startswith('/admin/') or path.startswith('/api/') or path.startswith('/rag/'):
            return response
        
        # Get the response content
        if not hasattr(response, 'content'):
            return response
        
        try:
            content = response.content.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            return response
        
        # Only inject if </body> tag exists
        if '</body>' not in content:
            return response
        
        # Don't inject if already present (avoid duplicates)
        if 'ragAssistantConfig' in content:
            return response
        
        # Build API URL
        api_url = "/rag/query/"
        try:
            from django.urls import reverse
            api_url = reverse("wagtail_context_search:query")
            api_url = request.build_absolute_uri(api_url)
        except Exception:
            api_url = request.build_absolute_uri("/rag/query/")
        
        # Get static URL prefix
        from django.conf import settings
        from django.contrib.staticfiles.storage import staticfiles_storage
        static_url = getattr(settings, 'STATIC_URL', '/static/')
        
        # Build static file URLs
        css_url = staticfiles_storage.url('wagtail_context_search/css/assistant.css')
        js_url = staticfiles_storage.url('wagtail_context_search/js/assistant.js')
        
        # Build the widget injection script
        widget_script = f"""
<!-- Wagtail Context Search Assistant -->
<script>
    window.ragAssistantConfig = {{
        apiUrl: '{api_url}',
        mode: '{config.get("ASSISTANT_UI_MODE", "both")}',
        position: '{config.get("ASSISTANT_POSITION", "bottom-right")}',
        theme: '{config.get("ASSISTANT_THEME", "light")}',
    }};
</script>
<link rel="stylesheet" href="{css_url}">
<script src="{js_url}"></script>
"""
        
        # Inject before </body>
        content = content.replace('</body>', widget_script + '</body>')
        
        # Update response
        response.content = content.encode('utf-8')
        
        return response
