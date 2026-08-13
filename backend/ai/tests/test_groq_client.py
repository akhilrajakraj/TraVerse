from unittest.mock import MagicMock, patch

import pytest

from ai.clients.groq_client import GroqClient
from ai.exceptions import LLMCallFailed


def _fake_response(content: str):
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content))]
    return response


@patch("ai.clients.groq_client.Groq")
def test_successful_call_returns_content(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.return_value = _fake_response("hello world")

    client = GroqClient(config=fake_config)
    result = client.call(system_prompt="sys", user_prompt="user")

    assert result == "hello world"


@patch("ai.clients.groq_client.Groq")
def test_retries_on_transient_error(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.side_effect = [
        ConnectionError("transient network blip"),
        _fake_response("recovered"),
    ]

    client = GroqClient(config=fake_config)
    result = client.call(system_prompt="sys", user_prompt="user")

    assert result == "recovered"
    assert mock_instance.chat.completions.create.call_count == 2


@patch("ai.clients.groq_client.Groq")
def test_raises_after_exhausting_retries(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.side_effect = ConnectionError("persistent failure")

    client = GroqClient(config=fake_config)

    with pytest.raises(LLMCallFailed):
        client.call(system_prompt="sys", user_prompt="user")

    assert mock_instance.chat.completions.create.call_count == 3


@patch("ai.clients.groq_client.Groq")
def test_structured_call_enables_json_object_mode(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.return_value = _fake_response('{"ok": true}')

    client = GroqClient(config=fake_config)
    client.call(system_prompt="Return JSON only.", user_prompt="Return an object.", json_mode=True)

    kwargs = mock_instance.chat.completions.create.call_args.kwargs
    assert kwargs["response_format"] == {"type": "json_object"}


@patch("ai.clients.groq_client.Groq")
def test_conversational_call_does_not_force_json_mode(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.return_value = _fake_response("hello")

    client = GroqClient(config=fake_config)
    client.call(system_prompt="You are conversational.", user_prompt="Say hello.")

    kwargs = mock_instance.chat.completions.create.call_args.kwargs
    assert "response_format" not in kwargs
