"""Upload pipeline: validate -> save -> extract -> chunk -> embed -> store."""
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.errors import AppError
from backend.models.database_models import Activity, Document
from backend.services.chunking_service import chunk_pages
from backend.services.pdf_service import extract_pages, has_pdf_signature, looks_scanned

SCANNED_MESSAGE = (
    "This PDF appears to be scanned or image-only, so no text could be extracted. "
    "OCR is required and is not supported in this version."
)


class DocumentService:
    def __init__(self, db: Session, settings: Settings, embedder, retrieval):
        self.db, self.settings, self.embedder, self.retrieval = db, settings, embedder, retrieval

    def upload(self, filename: str, data: bytes) -> Document:
        display_name = Path(filename or "document.pdf").name[:255]  # strips any path parts
        if not display_name.lower().endswith(".pdf"):
            raise AppError("Only PDF files are supported.", 400)
        if not data:
            raise AppError("The uploaded file is empty.", 400)
        if len(data) > self.settings.max_upload_size_bytes:
            raise AppError(f"File is too large. Maximum size is {self.settings.max_upload_size_mb} MB.", 413)
        if not has_pdf_signature(data):
            raise AppError("The file is not a valid PDF.", 400)

        upload_dir = self.settings.upload_directory.resolve()
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid.uuid4().hex}.pdf"  # generated, so no path traversal possible
        path = upload_dir / stored_name
        path.write_bytes(data)

        doc = Document(original_filename=display_name, stored_filename=stored_name,
                       file_size_bytes=len(data), status="processing")
        self.db.add(doc)
        self.db.commit()

        try:
            pages = extract_pages(path)
            doc.page_count = len(pages)
            if looks_scanned(pages):
                raise AppError(SCANNED_MESSAGE, 422)
            chunks = chunk_pages(pages)
            if not chunks:
                raise AppError("No usable text was found in this PDF.", 422)
            embeddings = self.embedder.embed([c.text for c in chunks])
            self.retrieval.add_chunks(doc.id, display_name, chunks, embeddings)
            doc.chunk_count = len(chunks)
            doc.status = "ready"
            self.db.add(Activity(activity_type="document_upload",
                                 description=f"Uploaded {display_name}", reference_id=doc.id))
        except Exception as exc:
            self.retrieval.delete_document(doc.id)  # no partial vectors
            path.unlink(missing_ok=True)
            doc.status = "failed"
            doc.error_message = exc.message if isinstance(exc, AppError) else "Processing failed unexpectedly."
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def list(self) -> list[Document]:
        return list(self.db.scalars(select(Document).order_by(Document.created_at.desc())))

    def get(self, document_id: str) -> Document:
        doc = self.db.get(Document, document_id)
        if not doc:
            raise AppError("Document not found.", 404)
        return doc

    def delete(self, document_id: str) -> None:
        doc = self.get(document_id)
        self.retrieval.delete_document(doc.id)
        (self.settings.upload_directory / doc.stored_filename).unlink(missing_ok=True)
        self.db.delete(doc)
        self.db.commit()