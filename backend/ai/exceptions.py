"""
Independent exception hierarchy for the ai/ package.

Deliberately does NOT import from apps.core.exceptions — see Chapter 11
Architecture Decision for why, even though both hierarchies are
structurally similar (a conscious mirroring, not accidental
duplication).
"""


class AIError(Exception):
    """
    Base class for all deliberate, expected errors raised within ai/.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ConfigurationError(AIError):
    """
    Raised when required AI-layer configuration (e.g. GROQ_API_KEY)
    is missing from the environment.
    """

    pass


class LLMCallFailed(AIError):
    """
    Raised when a call to the LLM provider fails after all retries
    are exhausted.
    """

    pass


class StructuredOutputInvalid(AIError):
    """
    Raised when a model's output cannot be coerced into the
    expected Pydantic schema, even after one correction retry.
    """

    pass