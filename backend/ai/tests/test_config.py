import pytest

from ai.config import load_config
from ai.exceptions import ConfigurationError


def test_get_groq_api_key_reads_from_environ(monkeypatch):
    monkeypatch.setenv(
        "GROQ_API_KEY",
        "abc123",
    )

    config = load_config()

    assert config.groq_api_key == "abc123"


def test_missing_api_key_raises_configuration_error(monkeypatch):
    monkeypatch.delenv(
        "GROQ_API_KEY",
        raising=False,
    )

    with pytest.raises(ConfigurationError):
        load_config()


def test_defaults_applied_when_optional_vars_missing(monkeypatch):
    monkeypatch.setenv(
        "GROQ_API_KEY",
        "abc123",
    )

    monkeypatch.delenv(
        "GROQ_MODEL_NAME",
        raising=False,
    )

    config = load_config()

    assert config.model_name == "llama-3.1-8b-instant"