from sqlalchemy.orm import Session

from backend.errors import AppError
from backend.models.database_models import Document
from backend.services.retrieval_service import RetrievedChunk


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def format_chunks(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(
        f"[{i}] (file: {c.filename}, page {c.page_number})\n{c.text}" for i, c in enumerate(chunks, 1)
    )


def chunk_to_source(index: int, chunk: RetrievedChunk, cited: bool = False) -> dict:
    return {
        "id": index, "document_id": chunk.document_id, "filename": chunk.filename,
        "page_number": chunk.page_number, "snippet": chunk.text[:300],
        "score": round(chunk.score, 3), "cited": cited,
    }


def get_ready_document(db: Session, document_id: str) -> Document:
    doc = db.get(Document, document_id)
    if not doc:
        raise AppError("Document not found.", 404)
    if doc.status != "ready":
        raise AppError(f"Document '{doc.original_filename}' is not ready to use ({doc.status}).", 400)
    return doc