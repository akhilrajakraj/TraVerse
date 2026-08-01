from django.apps import AppConfig


class TripsConfig(AppConfig):
    """
    Configuration for the Trips application.
    """

    default_auto_field = "django.db.models.BigAutoField"

    name = "apps.trips"

    verbose_name = "Trips"