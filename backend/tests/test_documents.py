from backend.tests.conftest import FakeEmbedder, make_pdf_bytes

BIO = "Photosynthesis converts light energy into chemical energy inside chloroplasts. " * 15
MITO = "Mitochondria produce ATP through cellular respiration. " * 15


def upload(client, data, name="notes.pdf"):
    return client.post("/api/documents/upload", files={"file": (name, data, "application/pdf")})


def test_upload_ready_and_retrievable(client, retrieval):
    r = upload(client, make_pdf_bytes([BIO, MITO]))
    assert r.status_code == 201
    doc = r.json()["data"]
    assert doc["status"] == "ready" and doc["page_count"] == 2 and doc["chunk_count"] >= 2
    q = FakeEmbedder().embed(["mitochondria ATP respiration"])[0]
    hits = retrieval.search(q, document_ids=[doc["id"]], top_k=3)
    assert hits and hits[0].page_number == 2 and hits[0].filename == "notes.pdf"


def test_list_and_get(client):
    a = upload(client, make_pdf_bytes([BIO]), "a.pdf").json()["data"]
    upload(client, make_pdf_bytes([MITO]), "b.pdf")
    assert len(client.get("/api/documents").json()["data"]) == 2
    assert client.get(f"/api/documents/{a['id']}").json()["data"]["original_filename"] == "a.pdf"


def test_delete_cleans_everything(client, retrieval, tmp_path):
    doc = upload(client, make_pdf_bytes([BIO])).json()["data"]
    uploads = tmp_path / "uploads"
    assert len(list(uploads.glob("*.pdf"))) == 1
    assert retrieval.count_for_document(doc["id"]) > 0
    assert client.delete(f"/api/documents/{doc['id']}").status_code == 200
    assert retrieval.count_for_document(doc["id"]) == 0
    assert list(uploads.glob("*.pdf")) == []
    assert client.get(f"/api/documents/{doc['id']}").status_code == 404


def test_rejects_non_pdf_extension(client):
    r = upload(client, b"hello", "notes.txt")
    assert r.status_code == 400 and r.json()["success"] is False


def test_rejects_fake_pdf(client):
    assert upload(client, b"just plain text", "fake.pdf").status_code == 400


def test_rejects_too_large_file(client):
    big = b"%PDF-" + b"0" * (1024 * 1024 + 10)  # test limit is 1 MB
    assert upload(client, big).status_code == 413


def test_scanned_pdf_is_marked_failed_with_ocr_message(client, retrieval, tmp_path):
    r = upload(client, make_pdf_bytes([""]))
    doc = r.json()["data"]
    assert doc["status"] == "failed" and "OCR" in doc["error_message"]
    assert doc["chunk_count"] == 0
    assert list((tmp_path / "uploads").glob("*.pdf")) == []


def test_get_missing_document_404(client):
    r = client.get("/api/documents/nope")
    assert r.status_code == 404 and r.json()["success"] is False