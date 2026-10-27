"""PDF text extraction with PyMuPDF."""
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from backend.errors import AppError

MIN_CHARS_PER_PAGE = 20  # average below this means the PDF is probably scanned images


@dataclass(frozen=True)
class PageText:
    page_number: int  # 1-based
    text: str


def has_pdf_signature(data: bytes) -> bool:
    return data[:5] == b"%PDF-"


def extract_pages(path: Path) -> list[PageText]:
    try:
        with fitz.open(path) as doc:
            if doc.needs_pass:
                raise AppError("This PDF is password-protected. Remove the password and retry.", 422)
            pages = [
                PageText(i, page.get_text("text").strip())
                for i, page in enumerate(doc, start=1)
            ]
    except AppError:
        raise
    except Exception:
        raise AppError("The file could not be read as a PDF. It may be corrupted.", 422) from None
    if not pages:
        raise AppError("The PDF has no pages.", 422)
    return pages


def looks_scanned(pages: list[PageText]) -> bool:
    total = sum(len(p.text) for p in pages)
    return total < MIN_CHARS_PER_PAGE * len(pages)