from pydantic import BaseModel
import pytest

from ai.exceptions import StructuredOutputInvalid
from ai.parsers.structured_output import parse_structured_output


class DemoSchema(BaseModel):
    """
    Simple schema used by parser tests.
    """

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


def test_invalid_after_repair_raises():
    with pytest.raises(
        StructuredOutputInvalid,
    ):
        parse_structured_output(
            raw_text="not json",
            schema=DemoSchema,
            repair_callback=lambda _: "still not json",
        )