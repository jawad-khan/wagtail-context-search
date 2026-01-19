"""
URL routing for RAG assistant API.
"""

from django.urls import path

from wagtail_context_search import views

app_name = "wagtail_context_search"

urlpatterns = [
    path("query/", views.query_view, name="query"),
    path("health/", views.health_view, name="health"),
]
