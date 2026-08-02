"""
AI-layer configuration, read directly from the process environment.

Deliberately does NOT import django.conf.settings — see Chapter 11
Architecture Decision.
"""

import os
from dataclasses import dataclass

from ai.exceptions import ConfigurationError


@dataclass(frozen=True)
class AIConfig:
    """
    Immutable AI configuration loaded from the process environment.
    """

    groq_api_key: str
    model_name: str
    request_timeout_seconds: float
    max_retries: int


def load_config() -> AIConfig:
    """
    Load AI configuration from environment variables.
    """

    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        raise ConfigurationError(
            "GROQ_API_KEY is not set in the environment. "
            "Add it to .env (see Chapter 1) before using the ai/ package."
        )

    return AIConfig(
        groq_api_key=api_key,
        model_name=os.environ.get(
            "GROQ_MODEL_NAME",
            "llama-3.1-8b-instant",
        ),
        request_timeout_seconds=float(
            os.environ.get(
                "GROQ_TIMEOUT_SECONDS",
                "30",
            )
        ),
        max_retries=int(
            os.environ.get(
                "GROQ_MAX_RETRIES",
                "3",
            )
        ),
    )