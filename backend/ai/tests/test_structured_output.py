from pydantic import BaseModel
import pytest

from ai.exceptions import StructuredOutputInvalid
from ai.parsers.structured_output import parse_structured_output


class DemoSchema(BaseModel):
    message: str


def test_valid_json_is_parsed():
    result = parse_structured_output(
        raw_text='{"message":"hello"}',
        schema=DemoSchema,
        repair_callback=lambda _: '{"message":"unused"}',
    )
    assert result.message == "hello"


def test_invalid_json_is_repaired():
    result = parse_structured_output(
        raw_text="this is not json",
        schema=DemoSchema,
        repair_callback=lambda _: '{"message":"fixed"}',
    )
    assert result.message == "fixed"


def test_repair_prompt_contains_exact_schema_and_instance_instructions():
    prompts: list[str] = []
    result = parse_structured_output(
        raw_text='{"message":"unterminated}',
        schema=DemoSchema,
        repair_callback=lambda prompt: prompts.append(prompt) or '{"message":"fixed"}',
    )
    assert result.message == "fixed"
    assert '"message"' in prompts[0]
    assert "REQUIRED JSON SCHEMA DEFINITION" in prompts[0].upper()
    assert "ORIGINAL MODEL RESPONSE" in prompts[0].upper()
    assert "DO NOT RETURN THIS SCHEMA" in prompts[0].upper()
    assert "ONE JSON OBJECT" in prompts[0].upper()


def test_schema_document_is_not_accepted_as_a_repaired_instance():
    schema_document = DemoSchema.model_json_schema()

    with pytest.raises(StructuredOutputInvalid):
        parse_structured_output(
            raw_text='{"unexpected":"shape"}',
            schema=DemoSchema,
            repair_callback=lambda _: __import__("json").dumps(schema_document),
        )


def test_invalid_after_repair_raises():
    with pytest.raises(StructuredOutputInvalid):
        parse_structured_output(
            raw_text="not json",
            schema=DemoSchema,
            repair_callback=lambda _: "still not json",
        )
