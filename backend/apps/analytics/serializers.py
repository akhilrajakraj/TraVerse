from rest_framework import serializers


class PlatformSummarySerializer(serializers.Serializer):
    total_trips = serializers.IntegerField()
    trips_by_status = serializers.DictField()
    total_agent_runs = serializers.IntegerField()
    agent_success_rate = serializers.FloatField()


class AgentPerformanceSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    succeeded = serializers.IntegerField()
    failed = serializers.IntegerField()
    needs_review = serializers.IntegerField()
    pending_or_running = serializers.IntegerField()
