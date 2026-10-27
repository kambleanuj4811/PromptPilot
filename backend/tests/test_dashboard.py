import json

from backend.tests.conftest import make_pdf_bytes

BIO = "Photosynthesis converts light energy into chemical energy inside chloroplasts. " * 15
MCQ = json.dumps({"questions": [{"question": "q?", "options": ["a", "b", "c", "d"],
                                 "correct_index": 0, "explanation": "e"}]})
VIVA = json.dumps({"questions": [{"question": "What?", "expected_points": ["p"]}]})


def stats(client):
    return client.get("/api/dashboard/stats").json()["data"]


def upload(client, pages):
    return client.post("/api/documents/upload",
                       files={"file": ("n.pdf", make_pdf_bytes(pages), "application/pdf")})


def test_empty_dashboard_has_zero_counts_and_no_activity(client):
    assert stats(client) == {"documents": 0, "documents_ready": 0, "study_sessions": 0,
                             "viva_sessions": 0, "viva_completed": 0, "prompt_comparisons": 0}
    assert client.get("/api/dashboard/activity").json()["data"] == []


def test_counts_come_from_stored_data(client, fake_provider):
    upload(client, [BIO])
    fake_provider.responses = [MCQ]
    client.post("/api/study/mcqs", json={"topic": "t", "count": 1})
    fake_provider.responses = [VIVA]
    client.post("/api/viva/start", json={"topic": "t", "difficulty": "easy", "count": 1})
    s = stats(client)
    assert (s["documents"], s["documents_ready"], s["study_sessions"]) == (1, 1, 1)
    assert (s["viva_sessions"], s["viva_completed"]) == (1, 0)


def test_activity_is_newest_first_and_limited(client, fake_provider):
    upload(client, [BIO])
    fake_provider.responses = [MCQ]
    client.post("/api/study/mcqs", json={"topic": "t", "count": 1})
    acts = client.get("/api/dashboard/activity").json()["data"]
    assert [a["type"] for a in acts] == ["study", "document_upload"]
    assert len(client.get("/api/dashboard/activity?limit=1").json()["data"]) == 1


def test_failed_upload_counts_as_document_but_creates_no_activity(client):
    upload(client, [""])  # blank page -> processing fails
    s = stats(client)
    assert s["documents"] == 1 and s["documents_ready"] == 0
    assert client.get("/api/dashboard/activity").json()["data"] == []