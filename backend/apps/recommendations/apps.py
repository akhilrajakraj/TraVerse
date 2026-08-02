"""
Application configuration for the Recommendations app.
"""

from django.apps import AppConfig


class RecommendationsConfig(AppConfig):
    """
    Configuration for the Recommendations application.
    """

    default_auto_field = "django.db.models.BigAutoField"

    name = "apps.recommendations"

    verbose_name = "Recommendations"

    def ready(self) -> None:
        """
        Import signal handlers during Django startup.

        Signals are introduced as part of the application lifecycle.
        Importing them here ensures they are registered exactly once
        when Django initializes the application registry.
        """

        import apps.recommendations.signals  # noqa: F401