import json

import pytest

CARD = json.dumps({"title": "T", "definition": "d", "key_points": ["a", "b"], "difficulty": "beginner"})


def run(client, technique_id, user_input=""):
    return client.post("/api/prompt-lab/run", json={"technique_id": technique_id, "user_input": user_input})


def test_techniques_are_listed(client):
    data = client.get("/api/prompt-lab/techniques").json()["data"]
    assert [t["id"] for t in data] == ["zero_shot", "few_shot", "role", "chaining",
                                       "structured", "context_aware", "validation"]
    for t in data:
        for key in ("name", "explanation", "example_prompt", "why", "default_input", "model_calls"):
            assert t[key]


@pytest.mark.parametrize("technique_id,responses,steps", [
    ("zero_shot", ["Three sentences."], 1),
    ("few_shot", ["Q: x\nA: y"], 1),
    ("role", ["plain", "examiner"], 2),
    ("chaining", ["a\nb\nc", "Q1\nQ2\nQ3"], 2),
    ("structured", [CARD], 1),
    ("context_aware", ["ATP."], 1),
    ("validation", [CARD], 1),
])
def test_each_technique_runs(client, fake_provider, technique_id, responses, steps):
    fake_provider.responses = list(responses)
    r = run(client, technique_id)
    data = r.json()["data"]
    assert r.status_code == 200 and len(data["steps"]) == steps and data["final_output"]


def test_chaining_feeds_step_one_into_step_two(client, fake_provider):
    fake_provider.responses = ["Concept A\nConcept B\nConcept C", "Questions"]
    run(client, "chaining")
    assert "Concept A" in fake_provider.calls[1]["prompt"]


def test_validation_repairs_invalid_output_once(client, fake_provider):
    fake_provider.responses = ["oops", CARD]
    data = run(client, "validation").json()["data"]
    assert data["validation"]["valid"] is True and data["validation"]["attempts"] == 2
    assert len(data["steps"]) == 2


def test_validation_reports_failure_without_looping(client, fake_provider):
    fake_provider.responses = ["oops"]
    data = run(client, "validation").json()["data"]
    assert data["validation"]["valid"] is False and data["validation"]["attempts"] == 2
    assert len(fake_provider.calls) == 2


def test_unknown_technique_rejected(client):
    assert run(client, "magic").status_code == 422


def test_blank_input_uses_default(client, fake_provider):
    techniques = client.get("/api/prompt-lab/techniques").json()["data"]
    default = next(t["default_input"] for t in techniques if t["id"] == "zero_shot")
    fake_provider.responses = ["x"]
    data = run(client, "zero_shot", "   ").json()["data"]
    assert default in data["steps"][0]["prompt"]


def test_structured_gives_up_after_retry_limit(client, fake_provider):
    fake_provider.responses = ['{"title": "x"}']
    r = run(client, "structured")
    assert r.status_code == 502 and len(fake_provider.calls) == 3


def test_context_is_fenced_as_untrusted(client, fake_provider):
    fake_provider.responses = ["x"]
    data = run(client, "context_aware").json()["data"]
    assert "<<<DOCUMENT START" in data["steps"][0]["prompt"]