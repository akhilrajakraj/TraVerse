"""
Application configuration for the AI Agents Django app.

This app is the ONLY Django application permitted to import from the
plain-Python ``ai`` package.

It acts as the bridge between:

- Django models
- Celery
- REST API
- LangGraph
- AI infrastructure

No other Django app should communicate directly with ``ai``.
"""

from django.apps import AppConfig


class AIAgentsConfig(AppConfig):
    """
    Configuration for the AI Agents application.
    """

    default_auto_field = "django.db.models.BigAutoField"

    name = "apps.ai_agents"

    verbose_name = "AI Agents"