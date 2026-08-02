"""
THE single door to the Groq LLM API.

Per Architecture Handbook §9.10, no agent (Chapter 12 onward) is
permitted to call the Groq SDK directly — every call goes through this
client.
"""

import logging

from groq import Groq
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ai.config import (
    AIConfig,
    load_config,
)
from ai.exceptions import LLMCallFailed

logger = logging.getLogger("ai.clients.groq")


class GroqClient:
    """
    Thin, focused wrapper around the Groq SDK.

    Owns:

    - client construction
    - timeout handling
    - retry/backoff

    Does NOT own:

    - prompt construction
    - output validation
    - parsing
    """

    def __init__(
        self,
        config: AIConfig | None = None,
    ):
        self._config = config or load_config()

        self._client = Groq(
            api_key=self._config.groq_api_key,
            timeout=self._config.request_timeout_seconds,
        )

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=8,
        ),
        reraise=True,
    )
    def _call(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> str:
        """
        Perform a single LLM call.

        Automatic retry is handled by the tenacity decorator.
        """

        response = self._client.chat.completions.create(
            model=self._config.model_name,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        return response.choices[0].message.content

    def call(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
    ) -> str:
        """
        Public interface used by every future AI agent.
        """

        try:
            return self._call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
            )

        except Exception as exc:
            logger.error(
                "Groq call failed after retries: %s",
                exc,
            )

            raise LLMCallFailed(
                f"LLM call failed after retries: {exc}"
            ) from exc