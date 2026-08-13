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
    assert client.call(system_prompt="sys", user_prompt="user", json_mode=False) == "hello world"


@patch("ai.clients.groq_client.Groq")
def test_retries_on_transient_error(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.side_effect = [ConnectionError("transient"), _fake_response("recovered")]
    client = GroqClient(config=fake_config)
    assert client.call(system_prompt="sys", user_prompt="user", json_mode=False) == "recovered"
    assert mock_instance.chat.completions.create.call_count == 2


@patch("ai.clients.groq_client.Groq")
def test_raises_after_exhausting_retries(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.side_effect = ConnectionError("persistent")
    client = GroqClient(config=fake_config)
    with pytest.raises(LLMCallFailed):
        client.call(system_prompt="sys", user_prompt="user", json_mode=False)
    assert mock_instance.chat.completions.create.call_count == 3


@patch("ai.clients.groq_client.Groq")
def test_structured_call_enables_json_object_mode(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.return_value = _fake_response('{"ok": true}')
    client = GroqClient(config=fake_config)
    client.call(system_prompt="Return JSON only.", user_prompt="Return an object.")
    assert mock_instance.chat.completions.create.call_args.kwargs["response_format"] == {"type": "json_object"}


@patch("ai.clients.groq_client.Groq")
def test_conversational_call_can_disable_json_mode(mock_groq_cls, fake_config):
    mock_instance = mock_groq_cls.return_value
    mock_instance.chat.completions.create.return_value = _fake_response("hello")
    client = GroqClient(config=fake_config)
    client.call(system_prompt="You are conversational.", user_prompt="Say hello.", json_mode=False)
    assert "response_format" not in mock_instance.chat.completions.create.call_args.kwargs
