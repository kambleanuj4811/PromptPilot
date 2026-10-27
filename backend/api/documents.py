from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.config import Settings, get_settings
from backend.database import get_db
from backend.dependencies import get_embedder, get_retrieval
from backend.models.schemas import ApiResponse, ok
from backend.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    original_filename: str
    file_size_bytes: int
    page_count: int | None
    chunk_count: int
    status: str
    error_message: str | None
    created_at: object


def get_document_service(db: Session = Depends(get_db), settings: Settings = Depends(get_settings),
                         embedder=Depends(get_embedder), retrieval=Depends(get_retrieval)):
    return DocumentService(db, settings, embedder, retrieval)


def _out(doc) -> dict:
    return DocumentOut.model_validate(doc).model_dump(mode="json")


@router.post("/upload", response_model=ApiResponse, status_code=201)
def upload(file: UploadFile = File(...), service: DocumentService = Depends(get_document_service),
           settings: Settings = Depends(get_settings)):
    data = file.file.read(settings.max_upload_size_bytes + 1)  # read at most limit+1 bytes
    return ok(_out(service.upload(file.filename, data)))


@router.get("", response_model=ApiResponse)
def list_documents(service: DocumentService = Depends(get_document_service)):
    return ok([_out(d) for d in service.list()])


@router.get("/{document_id}", response_model=ApiResponse)
def get_document(document_id: str, service: DocumentService = Depends(get_document_service)):
    return ok(_out(service.get(document_id)))


@router.delete("/{document_id}", response_model=ApiResponse)
def delete_document(document_id: str, service: DocumentService = Depends(get_document_service)):
    service.delete(document_id)
    return ok({"deleted": document_id})