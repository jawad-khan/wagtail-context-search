from django.apps import AppConfig


class WagtailContextSearchConfig(AppConfig):
    """App configuration for Wagtail Context Search."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "wagtail_context_search"
    verbose_name = "Wagtail Context Search"

    def ready(self):
        """Import signals when app is ready."""
        import wagtail_context_search.signals  # noqa
