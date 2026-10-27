"""Split page text into overlapping chunks. Chunks never cross pages, so every
chunk has an exact page number."""
from dataclasses import dataclass

from backend.services.pdf_service import PageText


@dataclass(frozen=True)
class Chunk:
    index: int
    page_number: int
    text: str


def split_text(text: str, size: int = 1000, overlap: int = 200) -> list[str]:
    if size <= 0 or overlap < 0 or overlap >= size // 2:
        raise ValueError("overlap must be >= 0 and smaller than half of chunk size")
    text = " ".join(text.split())
    if not text:
        return []
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = text.rfind(" ", start + size // 2, end)
            if cut != -1:
                end = cut
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)  # always moves forward
        if text[start - 1] != " ":  # begin on a word boundary
            nxt = text.find(" ", start)
            if nxt != -1 and nxt < end:
                start = nxt + 1
    return chunks


def chunk_pages(pages: list[PageText], size: int = 1000, overlap: int = 200) -> list[Chunk]:
    chunks: list[Chunk] = []
    for page in pages:
        for piece in split_text(page.text, size, overlap):
            chunks.append(Chunk(index=len(chunks), page_number=page.page_number, text=piece))
    return chunks