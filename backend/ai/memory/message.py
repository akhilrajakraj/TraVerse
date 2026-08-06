"""
Conversation memory domain models.

These models represent conversational history independently of Django,
LangGraph, or any LLM provider.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


MessageRole = Literal[
    "system",
    "user",
    "assistant",
    "tool",
]


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    """
    Immutable representation of a single conversation message.

    This model is intentionally framework-independent and serves as the
    canonical message object throughout the standalone AI package.
    """

    role: MessageRole

    content: str

    timestamp: datetime

    token_count: int | None = None