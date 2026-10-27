import pytest

from backend.errors import AppError
from backend.services.pdf_service import extract_pages, looks_scanned
from backend.tests.conftest import make_pdf_bytes


def test_extract_pages_returns_text_per_page(tmp_path):
    path = tmp_path / "a.pdf"
    path.write_bytes(make_pdf_bytes(["First page text about cells.", "Second page text about DNA."]))
    pages = extract_pages(path)
    assert [p.page_number for p in pages] == [1, 2]
    assert "cells" in pages[0].text and "DNA" in pages[1].text


def test_blank_pdf_looks_scanned(tmp_path):
    path = tmp_path / "blank.pdf"
    path.write_bytes(make_pdf_bytes([""]))
    assert looks_scanned(extract_pages(path))


def test_text_pdf_is_not_scanned(tmp_path):
    path = tmp_path / "text.pdf"
    path.write_bytes(make_pdf_bytes(["Real selectable text content on this page. " * 5]))
    assert not looks_scanned(extract_pages(path))


def test_corrupt_pdf_raises_app_error(tmp_path):
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"%PDF-1.4 this is garbage")
    with pytest.raises(AppError):
        extract_pages(path)