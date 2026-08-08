from django.urls import path

from apps.documents.views import PublicSharedItineraryView


app_name = "public_documents"


urlpatterns = [
    path(
        "share/<str:token>/",
        PublicSharedItineraryView.as_view(),
        name="shared-itinerary",
    ),
]