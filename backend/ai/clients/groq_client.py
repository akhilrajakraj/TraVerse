"""Single provider gateway for Groq LLM calls."""

import json
import logging
from typing import Callable

from groq import Groq
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ai.config import AIConfig, load_config
from ai.exceptions import LLMCallFailed

logger = logging.getLogger("ai.clients.groq")


class GroqClient:
    """Thin Groq wrapper owning provider calls, retries and JSON mode."""

    def __init__(self, config: AIConfig | None = None):
        self._config = config or load_config()
        self._client = Groq(api_key=self._config.groq_api_key, timeout=self._config.request_timeout_seconds)

    @retry(retry=retry_if_exception_type(Exception), stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8), reraise=True)
    def _call_raw(self, *, messages: list[dict], temperature: float, tools: list[dict] | None = None, json_mode: bool = False):
        kwargs = {"model": self._config.model_name, "temperature": temperature, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        return self._client.chat.completions.create(**kwargs)

    def call(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.3, json_mode: bool = True) -> str:
        try:
            response = self._call_raw(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=temperature,
                json_mode=json_mode,
            )
            return response.choices[0].message.content
        except Exception as exc:
            logger.error("Groq call failed after retries: %s", exc)
            raise LLMCallFailed(f"LLM call failed after retries: {exc}") from exc

    def call_with_tools(self, *, system_prompt: str, user_prompt: str, tools: list[dict], tool_executor: Callable[[str, dict], str], temperature: float = 0.2, json_mode: bool = True) -> str:
        try:
            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
            first_response = self._call_raw(messages=messages, temperature=temperature, tools=tools, json_mode=False)
            message = first_response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None)
            if not tool_calls:
                return message.content
            messages.append({"role": "assistant", "content": message.content or "", "tool_calls": tool_calls})
            for tool_call in tool_calls:
                name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                result = tool_executor(name, arguments)
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": name, "content": result})
            final_response = self._call_raw(messages=messages, temperature=temperature, json_mode=json_mode)
            return final_response.choices[0].message.content
        except Exception as exc:
            logger.error("Groq tool-calling call failed: %s", exc)
            raise LLMCallFailed(f"LLM tool-calling call failed: {exc}") from exc
