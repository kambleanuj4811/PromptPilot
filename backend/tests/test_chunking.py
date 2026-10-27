import pytest

from backend.services.chunking_service import chunk_pages, split_text
from backend.services.pdf_service import PageText


def test_short_text_is_one_chunk():
    assert split_text("hello   world", size=100, overlap=20) == ["hello world"]


def test_chunks_respect_size_and_overlap():
    text = " ".join(f"word{i}" for i in range(300))
    chunks = split_text(text, size=100, overlap=20)
    assert len(chunks) > 3
    assert all(len(c) <= 100 for c in chunks)
    for a, b in zip(chunks, chunks[1:]):
        assert a.split()[-1] in b.split()  # consecutive chunks overlap


def test_chunk_pages_keeps_page_numbers():
    pages = [PageText(1, "alpha " * 300), PageText(2, "beta"), PageText(3, "")]
    chunks = chunk_pages(pages, size=200, overlap=40)
    assert [c.index for c in chunks] == list(range(len(chunks)))
    assert chunks[-1].page_number == 2 and chunks[-1].text == "beta"
    assert all(c.page_number == 1 for c in chunks[:-1])
    assert all(c.text for c in chunks)  # no empty chunks, empty page skipped


def test_invalid_overlap_rejected():
    with pytest.raises(ValueError):
        split_text("x", size=100, overlap=100)