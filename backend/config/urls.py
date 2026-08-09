"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import include, path

from common.health import health_check
from .views import system_info


urlpatterns = [
    path("admin/", admin.site.urls),
    path("system-info/", system_info),
    path("health/", health_check),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/profiles/", include("apps.profiles.urls")),
    path("api/destinations/", include("apps.destinations.urls")),
    path("api/trips/", include("apps.trips.urls")),
    path("api/trips/", include("apps.bookings.urls")),
    path("api/itinerary/", include("apps.itinerary.urls")),
    path("api/budget/", include("apps.budget.urls")),
    path("api/recommendations/", include("apps.recommendations.urls")),
    path("api/ai_agents/", include("apps.ai_agents.urls")),
    path("api/chat/", include("apps.chat.urls")),
    path("api/documents/", include("apps.documents.urls")),
    path("api/v1/public/", include("apps.documents.public_urls")),
    path("api/notifications/", include("apps.notifications.urls")),
]
