"""
Application configuration for the Budget application.
"""

from django.apps import AppConfig


class BudgetConfig(AppConfig):
    """
    Configuration for the Budget application.

    Signals are registered during application startup to keep
    Budget and Trip data synchronized automatically.
    """

    name = "apps.budget"

    verbose_name = "Budget"

    def ready(self) -> None:
        """
        Register signal handlers.

        Importing the signals module here ensures Django connects
        every receiver exactly once after the application registry
        has been fully initialized.
        """

        import apps.budget.signals  # noqa: F401