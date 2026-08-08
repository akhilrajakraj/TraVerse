from django.urls import path

from apps.documents.views import (
    CreateShareLinkView,
    GenerateItineraryPDFView,
    RevokeShareLinkView,
)


app_name = "documents"


urlpatterns = [
    path(
        "trips/<uuid:pk>/pdf/",
        GenerateItineraryPDFView.as_view(),
        name="trip-pdf",
    ),
    path(
        "trips/<uuid:pk>/share-link/",
        CreateShareLinkView.as_view(),
        name="create-share-link",
    ),
    path(
        "trips/<uuid:pk>/share-link/<uuid:document_id>/revoke/",
        RevokeShareLinkView.as_view(),
        name="revoke-share-link",
    ),
]