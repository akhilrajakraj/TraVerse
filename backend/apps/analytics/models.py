"""
Models for the analytics app.

Intentionally empty: analytics is a read-only consumer of data owned by
other applications. Computed analytics are cached temporarily in Redis
through Django's cache framework; no AnalyticsSnapshot model is needed.
"""
