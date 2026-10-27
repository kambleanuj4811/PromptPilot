import json

from backend.tests.conftest import make_pdf_bytes

PAPER = (
    "Research objectives: the aim and purpose of this study is to test a hypothesis about sleep. "
    "Methodology: the methods approach used a dataset and a clear procedure for measurement. "
    "Results: the key findings show outcomes and performance improved. "
    "Limitations: threats to validity and future work are small sample weaknesses. "
    "Conclusion: the contributions and summary show implications. "
) * 5
QUOTE = "the aim and purpose of this study is to test a hypothesis about sleep"


def upload(client, data=None, name="paper.pdf"):
    data = data or make_pdf_bytes([PAPER])
    return client.post("/api/documents/upload", files={"file": (name, data, "application/pdf")}).json()["data"]["id"]


def empty():
    return {"found_in_document": False, "findings": [], "interpretation": ""}


def analysis_json(quote=QUOTE):
    objectives = {"found_in_document": True, "interpretation": "Seems exploratory.",
                  "findings": [{"statement": "The study tests a sleep hypothesis.", "quote": quote, "source": 1}]}
    return json.dumps({"overview": "A sleep study.", "objectives": objectives, "methodology": empty(),
                       "key_findings": empty(), "limitations": empty(), "conclusions": empty()})


def test_analyze_keeps_verified_findings_with_page_numbers(client, fake_provider):
    doc_id = upload(client)
    fake_provider.responses = [analysis_json()]
    r = client.post("/api/research/analyze", json={"document_id": doc_id})
    data = r.json()["data"]
    finding = data["analysis"]["objectives"]["findings"][0]
    assert r.status_code == 200 and data["analysis"]["objectives"]["found_in_document"] is True
    assert finding["page_number"] == 1 and finding["filename"] == "paper.pdf"
    assert data["analysis"]["methodology"]["found_in_document"] is False
    assert data["analysis"]["overview"] and data["disclaimer"]


def test_fabricated_quote_is_removed_and_reported(client, fake_provider):
    doc_id = upload(client)
    fake_provider.responses = [analysis_json(quote="the experiment achieved 99.7 percent accuracy on ImageNet")]
    data = client.post("/api/research/analyze", json={"document_id": doc_id}).json()["data"]
    assert data["analysis"]["objectives"]["found_in_document"] is False
    assert data["analysis"]["objectives"]["findings"] == []
    assert any("removed" in n for n in data["notes"])


def test_summarize(client, fake_provider):
    doc_id = upload(client)
    fake_provider.responses = [json.dumps({"summary": "A sleep study.", "key_points": ["Tests a hypothesis"]})]
    data = client.post("/api/research/summarize", json={"document_id": doc_id}).json()["data"]
    assert data["summary"]["key_points"] and data["sources"]


def test_unknown_document_404(client):
    assert client.post("/api/research/analyze", json={"document_id": "missing"}).status_code == 404


def test_failed_document_cannot_be_analyzed(client):
    doc_id = upload(client, make_pdf_bytes([""]), "scan.pdf")  # blank page -> status failed
    r = client.post("/api/research/analyze", json={"document_id": doc_id})
    assert r.status_code == 400 and r.json()["success"] is False


def test_missing_document_id_rejected(client):
    assert client.post("/api/research/analyze", json={}).status_code == 422


def test_paper_text_is_fenced_as_untrusted(client, fake_provider):
    doc_id = upload(client)
    fake_provider.responses = [analysis_json()]
    client.post("/api/research/analyze", json={"document_id": doc_id})
    call = fake_provider.calls[0]
    assert "untrusted" in call["system"].lower()
    assert "<<<DOCUMENT START" in call["prompt"]