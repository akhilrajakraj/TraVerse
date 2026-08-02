"""
Shared pytest fixtures for the ai/ test suite.

Plain pytest fixtures — no Django test database, no Django fixtures.
"""

from unittest.mock import MagicMock

import pytest

from ai.config import AIConfig


@pytest.fixture
def fake_config() -> AIConfig:
    """
    Return a fake AI configuration for tests.
    """

    return AIConfig(
        groq_api_key="test-key-not-real",
        model_name="test-model",
        request_timeout_seconds=5.0,
        max_retries=3,
    )


@pytest.fixture
def mock_groq_sdk_client():
    """
    Fake stand-in for the real Groq SDK client.

    No test should ever perform a real API call.
    """

    return MagicMock()