import json

import pytest

from backend.tests.conftest import make_pdf_bytes

BIO = "Photosynthesis converts light energy into chemical energy inside chloroplasts. " * 15


def mcq(n, options=4):
    return json.dumps({"questions": [
        {"question": f"Question {i}?", "options": [f"opt{j}" for j in range(options)],
         "correct_index": 1, "explanation": "Because."} for i in range(n)]})


def post(client, op, **body):
    return client.post(f"/api/study/{op}", json=body)


def test_mcqs_valid(client, fake_provider):
    fake_provider.responses = [mcq(2)]
    r = post(client, "mcqs", topic="Photosynthesis", count=2)
    data = r.json()["data"]
    assert r.status_code == 200 and len(data["result"]["questions"]) == 2
    assert data["session_id"]


def test_mcq_invalid_output_is_repaired(client, fake_provider):
    fake_provider.responses = [mcq(2, options=3), mcq(2)]  # 3 options is invalid
    r = post(client, "mcqs", topic="Photosynthesis", count=2)
    assert r.status_code == 200 and len(fake_provider.calls) == 2


def test_mcq_gives_up_after_retry_limit(client, fake_provider):
    fake_provider.responses = [mcq(2, options=3)]
    r = post(client, "mcqs", topic="Photosynthesis", count=2)
    assert r.status_code == 502 and r.json()["success"] is False
    assert len(fake_provider.calls) == 3


def test_extra_mcqs_are_trimmed(client, fake_provider):
    fake_provider.responses = [mcq(3)]
    data = post(client, "mcqs", topic="Photosynthesis", count=2).json()["data"]
    assert len(data["result"]["questions"]) == 2


def test_missing_mcqs_add_a_note(client, fake_provider):
    fake_provider.responses = [mcq(1)]
    data = post(client, "mcqs", topic="Photosynthesis", count=3).json()["data"]
    assert data["notes"]


def test_missing_topic_rejected(client):
    r = post(client, "explain", topic="  ")
    assert r.status_code == 422 and r.json()["success"] is False


def test_summarize_needs_text_or_document(client):
    assert post(client, "summarize").status_code == 422


def test_invalid_level_rejected(client):
    assert post(client, "explain", topic="x", academic_level="wizard").status_code == 422


def test_pasted_notes_are_fenced_as_untrusted(client, fake_provider):
    fake_provider.responses = [json.dumps({"title": "T", "summary": "s", "key_points": ["a"]})]
    r = post(client, "summarize", text="Cells are the basic unit of life.")
    assert r.status_code == 200
    assert "<<<DOCUMENT START" in fake_provider.calls[0]["prompt"]


def test_explain_with_document_uses_retrieved_context(client, fake_provider):
    doc_id = client.post("/api/documents/upload", files={
        "file": ("bio.pdf", make_pdf_bytes([BIO]), "application/pdf")}).json()["data"]["id"]
    fake_provider.responses = [json.dumps({
        "title": "T", "overview": "o", "key_points": ["a"], "example": "e",
        "common_mistakes": [], "summary": "s"})]
    data = post(client, "explain", topic="photosynthesis chloroplasts light energy",
                document_id=doc_id).json()["data"]
    assert data["sources"] and "DOCUMENT CONTEXT" in fake_provider.calls[0]["prompt"]


def test_unknown_document_404(client):
    assert post(client, "explain", topic="x", document_id="missing").status_code == 404


@pytest.mark.parametrize("op,body,output", [
    ("explain", {"topic": "t"}, {"title": "T", "overview": "o", "key_points": ["a"],
                                 "example": "e", "common_mistakes": [], "summary": "s"}),
    ("summarize", {"text": "Some notes."}, {"title": "T", "summary": "s", "key_points": ["a"]}),
    ("revision-notes", {"topic": "t"}, {"title": "T", "sections": [{"heading": "h", "points": ["p"]}],
                                        "key_terms": [{"term": "t", "definition": "d"}]}),
    ("questions", {"topic": "t", "count": 1}, {"questions": [
        {"question": "q", "model_answer": "a", "marks": 2}]}),
    ("exam-answers", {"topic": "Explain osmosis"}, {"question": "q", "introduction": "i",
        "sections": [{"heading": "h", "content": "c"}], "conclusion": "c", "keywords": ["k"]}),
])
def test_every_operation_returns_validated_result(client, fake_provider, op, body, output):
    fake_provider.responses = [json.dumps(output)]
    r = post(client, op, **body)
    assert r.status_code == 200 and r.json()["data"]["result"]