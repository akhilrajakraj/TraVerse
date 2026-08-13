"""
Helpers for validating structured LLM output.

This module converts raw LLM responses into validated Pydantic models.
If the first validation fails, a single schema-aware repair attempt is
performed using a caller-supplied callback.
"""

from __future__ import annotations

import json
import logging
from typing import Callable, Type, TypeVar

from pydantic import BaseModel, ValidationError

from ai.exceptions import StructuredOutputInvalid

logger = logging.getLogger("ai.parsers.structured_output")

SchemaType = TypeVar("SchemaType", bound=BaseModel)


def _clean_response(text: str) -> str:
    """Remove common Markdown code fences from model output."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def parse_structured_output(
    *,
    raw_text: str,
    schema: Type[SchemaType],
    repair_callback: Callable[[str], str],
) -> SchemaType:
    """Parse and validate structured LLM output with one schema-aware repair."""
    try:
        cleaned = _clean_response(raw_text)
        data = json.loads(cleaned)
        return schema.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as first_error:
        logger.warning(
            "Structured output validation failed. Attempting automatic repair."
        )

        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        repair_prompt = (
            "Repair the supplied AI response. Return ONLY one valid JSON object "
            "that validates against the exact schema below. Do not add Markdown, "
            "comments, explanations, trailing commas, or additional fields. "
            "Preserve valid information from the original response and repair "
            "truncated strings, missing quotes, commas, braces, or other JSON "
            "syntax errors.\n\n"
            "REQUIRED JSON SCHEMA:\n"
            f"{schema_json}\n\n"
            "ORIGINAL RESPONSE:\n"
            f"{raw_text}"
        )

        repaired_text = repair_callback(repair_prompt)

        try:
            repaired = _clean_response(repaired_text)
            repaired_data = json.loads(repaired)
            return schema.model_validate(repaired_data)
        except (json.JSONDecodeError, ValidationError) as second_error:
            logger.error("Structured output repair failed.")
            raise StructuredOutputInvalid(
                "Unable to produce valid structured output. "
                f"Initial error: {first_error}; "
                f"Repair error: {second_error}"
            ) from second_error
