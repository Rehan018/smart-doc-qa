from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.document import (
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    service = DocumentService(db)
    return await service.upload_document(file)


@router.get("/{document_id}", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    service = DocumentService(db)
    return service.get_document_status(document_id)