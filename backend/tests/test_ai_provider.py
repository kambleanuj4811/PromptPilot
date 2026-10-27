import pytest
from pydantic import BaseModel

from backend.services.ai_provider import AIInvalidResponseError
from backend.services.validation_service import extract_json
from backend.tests.conftest import FakeProvider


class Demo(BaseModel):
    answer: str
    confidence: int


def test_extract_json_handles_fences_and_chatter():
    assert extract_json('Here:\n```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"a": 2} hope that helps') == {"a": 2}
    with pytest.raises(ValueError):
        extract_json("no json here")


def test_structured_valid_first_try():
    p = FakeProvider(['{"answer": "x", "confidence": 3}'])
    assert p.generate_structured("q", Demo).confidence == 3
    assert len(p.calls) == 1


def test_structured_repairs_after_bad_output():
    p = FakeProvider(["not json", '{"answer": "x", "confidence": 3}'])
    assert p.generate_structured("q", Demo).answer == "x"
    assert len(p.calls) == 2
    assert "invalid" in p.calls[1]["prompt"].lower()


def test_structured_stops_after_retry_limit():
    p = FakeProvider(['{"answer": "x"}'])  # always missing "confidence"
    with pytest.raises(AIInvalidResponseError):
        p.generate_structured("q", Demo, max_retries=2)
    assert len(p.calls) == 3  # 1 try + 2 retries, never more