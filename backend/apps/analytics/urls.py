from django.urls import path

from apps.analytics.views import AgentPerformanceView, PlatformSummaryView

app_name = "analytics"

urlpatterns = [
    path(
        "platform-summary/",
        PlatformSummaryView.as_view(),
        name="platform-summary",
    ),
    path(
        "agent-performance/",
        AgentPerformanceView.as_view(),
        name="agent-performance",
    ),
]
