"""
Test settings for Wagtail Context Search tests.
"""

import os

SECRET_KEY = "test-secret-key-for-testing-only"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "wagtail",
    "wagtail.models",
    "wagtail_context_search",
]

MIDDLEWARE = []

ROOT_URLCONF = "tests.urls"

USE_TZ = True

WAGTAIL_CONTEXT_SEARCH = {
    "LLM_BACKEND": "openai",
    "EMBEDDER_BACKEND": "openai",
    "VECTOR_DB_BACKEND": "chroma",
    "ASSISTANT_ENABLED": True,
}
