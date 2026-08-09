from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics import caching
from apps.analytics.serializers import (
    AgentPerformanceSerializer,
    PlatformSummarySerializer,
)


class PlatformSummaryView(APIView):
    """Return platform analytics to staff users only."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        summary = caching.get_cached_platform_summary()
        return Response(PlatformSummarySerializer(summary).data)


class AgentPerformanceView(APIView):
    """Return AI execution analytics to staff users only."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        summary = caching.get_cached_agent_performance_summary()
        return Response(AgentPerformanceSerializer(summary).data)
