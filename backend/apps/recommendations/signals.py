"""
Signal handlers for the Recommendations application.

Chapter 10 currently defines no model signals.

This module exists so AppConfig.ready() can safely import it during
application startup. Future chapters may register recommendation-related
signals here without requiring changes to the application configuration.
"""