from backend.services.chunking_service import Chunk
from backend.tests.conftest import FakeEmbedder

emb = FakeEmbedder()


def _add(retrieval, doc_id, name, texts):
    chunks = [Chunk(index=i, page_number=i + 1, text=t) for i, t in enumerate(texts)]
    retrieval.add_chunks(doc_id, name, chunks, emb.embed([c.text for c in chunks]))


def _setup(retrieval):
    _add(retrieval, "a", "bio.pdf", ["photosynthesis uses chlorophyll and light", "plants make sugar"])
    _add(retrieval, "b", "db.pdf", ["sql databases store tables", "photosynthesis is not covered here"])


def test_search_filters_by_document(retrieval):
    _setup(retrieval)
    q = emb.embed(["photosynthesis"])[0]
    only_b = retrieval.search(q, document_ids=["b"], top_k=5)
    assert only_b and all(h.document_id == "b" for h in only_b)
    only_a = retrieval.search(q, document_ids=["a"], top_k=5)
    assert only_a and all(h.document_id == "a" for h in only_a)
    assert only_a[0].filename == "bio.pdf" and only_a[0].page_number == 1


def test_delete_removes_vectors(retrieval):
    _setup(retrieval)
    assert retrieval.count_for_document("a") == 2
    retrieval.delete_document("a")
    assert retrieval.count_for_document("a") == 0
    assert retrieval.count_for_document("b") == 2


def test_empty_scope_returns_nothing(retrieval):
    _setup(retrieval)
    assert retrieval.search(emb.embed(["photosynthesis"])[0], document_ids=[]) == []