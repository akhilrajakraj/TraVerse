"""
Application configuration for the Profiles application.
"""

from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """
    Configuration for the Profiles application.
    """

    default_auto_field = "django.db.models.BigAutoField"

    name = "apps.profiles"

    def ready(self):
        """
        Register signal handlers.
        """

        import apps.profiles.signals  # noqa: F401