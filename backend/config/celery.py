"""
Celery application configuration.

This module creates the global Celery application used throughout
TraVerse.

Responsibilities
----------------
- Configure Celery from Django settings.
- Automatically discover tasks from installed apps.
- Provide the application instance for workers and beat.

The Celery application is intentionally initialized separately from
Django's WSGI/ASGI entry points.
"""

from __future__ import annotations

import os

from celery import Celery


#
# Ensure Celery uses the Django settings module.
#
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

#
# Create the Celery application.
#
app = Celery(
    "traverse",
)

#
# Load configuration from Django settings.
#
app.config_from_object(
    "django.conf:settings",
    namespace="CELERY",
)

#
# Automatically discover tasks.py from installed apps.
#
app.autodiscover_tasks()