import json

import pytest

from backend.dependencies import get_ai_provider
from backend.main import app
from backend.services.ai_provider import AIQuotaError
from backend.tests.conftest import FakeProvider

CRITERIA = ["accuracy", "completeness", "relevance", "consistency", "formatting"]
PROMPT_A = "Answer clearly. MARK_A"
PROMPT_B = "Answer briefly. MARK_B"


def judge_json(level):
    item = {"score": level, "justification": "ok", "issues": []}
    return json.dumps({c: item for c in CRITERIA})


class RoutedProvider(FakeProvider):
    """Candidate calls are routed by the marker in the system prompt. Judge calls (json_mode)
    score 9 when the response contains GOODANSWER, otherwise 4."""

    def __init__(self, outputs, judge_override=None):
        super().__init__()
        self.outputs = outputs
        self.judge_override = judge_override

    def generate_text(self, prompt, system=None, temperature=None, json_mode=False):
        self.calls.append({"prompt": prompt, "system": system, "json_mode": json_mode})
        if not json_mode:
            for marker, text in self.outputs.items():
                if marker in (system or ""):
                    return text
            raise AssertionError("unexpected candidate call")
        if self.judge_override is not None:
            return self.judge_override
        return judge_json(9) if "GOODANSWER" in prompt else judge_json(4)


class QuotaProvider(FakeProvider):
    def generate_text(self, *args, **kwargs):
        raise AIQuotaError("quota reached")


def compare(client, provider, **overrides):
    app.dependency_overrides[get_ai_provider] = lambda: provider
    body = {"prompt_a": PROMPT_A, "prompt_b": PROMPT_B, "test_questions": ["What is a cell?"]}
    body.update(overrides)
    return client.post("/api/evaluation/compare", json=body)


def test_compare_scores_and_picks_winner(client):
    provider = RoutedProvider({"MARK_A": "GOODANSWER about cells", "MARK_B": "weak"})
    r = compare(client, provider, test_questions=["What is a cell?", "What is DNA?"])
    data = r.json()["data"]
    assert r.status_code == 201 and len(data["results"]) == 2
    first = data["results"][0]
    assert first["a"]["overall"] == 9.0 and first["b"]["overall"] == 4.0
    assert first["a"]["scores"]["accuracy"]["justification"] == "ok"
    s = data["summary"]
    assert s["winner"] == "A" and s["variants"]["A"]["overall"] == 9.0
    assert s["variants"]["B"]["criteria"]["accuracy"] == 4.0
    assert len(provider.calls) == 8  # 2 questions x 2 prompts x (1 run + 1 judge)
    assert client.get("/api/dashboard/stats").json()["data"]["prompt_comparisons"] == 1


def test_json_checks_override_formatting_score(client):
    provider = RoutedProvider({"MARK_A": '{"answer": "GOODANSWER"}',
                               "MARK_B": '```json\n{"answer": "weak"}\n```'})
    r = compare(client, provider, expected_format="json", required_fields=["answer"])
    res = r.json()["data"]["results"][0]
    assert res["a"]["scores"]["formatting"]["score"] == 10.0
    assert res["b"]["scores"]["formatting"]["score"] == 0.0
    assert [c["name"] for c in res["b"]["checks"] if not c["passed"]] == ["valid_json", "required_fields"]
    assert res["a"]["overall"] == 9.2 and res["b"]["overall"] == 3.2


def test_max_words_check(client):
    provider = RoutedProvider({"MARK_A": "GOODANSWER one two", "MARK_B": "weak one two three four"})
    res = compare(client, provider, max_words=3).json()["data"]["results"][0]
    assert res["a"]["scores"]["formatting"]["score"] == 10.0
    assert res["b"]["scores"]["formatting"]["score"] == 0.0
    assert [c for c in res["b"]["checks"] if c["name"] == "max_words"][0]["passed"] is False


def test_unparseable_judge_output_marks_response_unscored(client):
    provider = RoutedProvider({"MARK_A": "GOODANSWER", "MARK_B": "weak"}, judge_override="not json")
    r = compare(client, provider)
    data = r.json()["data"]
    a = data["results"][0]["a"]
    assert r.status_code == 201
    assert a["scores"] is None and a["overall"] is None and a["error"]
    assert data["summary"]["winner"] == "unavailable"
    assert len(provider.calls) == 8  # 2 runs + 2 judges x 3 attempts


def test_empty_response_is_not_judged(client):
    provider = RoutedProvider({"MARK_A": "", "MARK_B": "GOODANSWER"})
    data = compare(client, provider).json()["data"]
    a = data["results"][0]["a"]
    assert a["scores"] is None and a["checks"][0]["passed"] is False
    assert data["results"][0]["b"]["overall"] == 9.0
    assert data["summary"]["winner"] == "unavailable"
    assert len(provider.calls) == 3  # A run, B run, B judge


def test_similar_scores_are_a_tie(client):
    provider = RoutedProvider({"MARK_A": "GOODANSWER one", "MARK_B": "GOODANSWER two"})
    assert compare(client, provider).json()["data"]["summary"]["winner"] == "tie"


@pytest.mark.parametrize("overrides", [
    {"test_questions": []},
    {"test_questions": ["a", "b", "c", "d"]},
    {"test_questions": ["   "]},
    {"expected_format": "text", "required_fields": ["answer"]},
])
def test_invalid_requests_rejected(client, overrides):
    r = compare(client, RoutedProvider({}), **overrides)
    assert r.status_code == 422 and r.json()["success"] is False


def test_history_lists_newest_first(client):
    provider = RoutedProvider({"MARK_A": "GOODANSWER", "MARK_B": "weak"})
    assert client.get("/api/evaluation/history").json()["data"] == []
    first_id = compare(client, provider).json()["data"]["id"]
    second_id = compare(client, provider).json()["data"]["id"]
    history = client.get("/api/evaluation/history").json()["data"]
    assert [h["id"] for h in history] == [second_id, first_id]
    assert history[0]["winner"] == "A" and history[0]["question_count"] == 1
    detail = client.get(f"/api/evaluation/{first_id}").json()["data"]
    assert detail["prompt_a"] == PROMPT_A and detail["results"][0]["question"] == "What is a cell?"


def test_unknown_evaluation_404(client):
    r = client.get("/api/evaluation/nope")
    assert r.status_code == 404 and r.json()["success"] is False


def test_judge_is_separate_and_fences_untrusted_text(client):
    provider = RoutedProvider({"MARK_A": "GOODANSWER", "MARK_B": "weak"})
    compare(client, provider)
    run_call, judge_call = provider.calls[0], provider.calls[1]
    assert run_call["system"] == PROMPT_A and run_call["json_mode"] is False
    assert "MARK_A" not in judge_call["system"] and "untrusted" in judge_call["system"].lower()
    assert "<<<AI RESPONSE START" in judge_call["prompt"]
    assert "<<<INSTRUCTIONS GIVEN TO THE AI START" in judge_call["prompt"]


def test_quota_error_aborts_and_saves_nothing(client):
    r = compare(client, QuotaProvider())
    assert r.status_code == 429 and r.json()["success"] is False
    assert client.get("/api/evaluation/history").json()["data"] == []