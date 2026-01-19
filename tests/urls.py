"""
Test URL configuration.
"""

from django.urls import include, path

urlpatterns = [
    path("rag/", include("wagtail_context_search.urls")),
]
