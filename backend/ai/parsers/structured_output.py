"""Helpers for validating and repairing structured LLM output."""

from __future__ import annotations

import json
import logging
from typing import Callable, Type, TypeVar

from pydantic import BaseModel, ValidationError

from ai.exceptions import StructuredOutputInvalid

logger = logging.getLogger("ai.parsers.structured_output")
SchemaType = TypeVar("SchemaType", bound=BaseModel)


def _clean_response(text: str) -> str:
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
    """Parse structured output and make one schema-aware repair attempt."""
    try:
        return schema.model_validate(json.loads(_clean_response(raw_text)))
    except (json.JSONDecodeError, ValidationError) as first_error:
        logger.warning("Structured output validation failed. Attempting automatic repair.")

        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        repair_prompt = (
            "Repair the supplied AI response. Return ONLY one valid JSON object "
            "that validates against the exact schema below. Do not return Markdown, "
            "comments, explanations, trailing commas, or additional fields. Preserve "
            "valid information and repair truncated strings, missing quotes, commas, "
            "braces, or other JSON syntax errors.\n\n"
            "REQUIRED JSON SCHEMA:\n"
            f"{schema_json}\n\n"
            "ORIGINAL RESPONSE:\n"
            f"{raw_text}"
        )

        try:
            repaired_text = repair_callback(repair_prompt)
            return schema.model_validate(json.loads(_clean_response(repaired_text)))
        except (json.JSONDecodeError, ValidationError) as second_error:
            logger.error("Structured output repair failed.")
            raise StructuredOutputInvalid(
                "Unable to produce valid structured output. "
                f"Initial error: {first_error}; Repair error: {second_error}"
            ) from second_error
