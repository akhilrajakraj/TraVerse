"""
Configuration package.

Importing the Celery application here ensures it is loaded whenever
Django starts.
"""

from .celery import app as celery_app

__all__ = [
    "celery_app",
]