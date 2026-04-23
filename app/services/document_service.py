import os
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.document import DocumentStatus
from app.db.models.job import JobStatus
from app.repositories.document_repository import DocumentRepository
from app.repositories.job_repository import JobRepository
from app.utils.file_utils import (
    ensure_directory,
    generate_stored_filename,
    get_file_extension,
    is_allowed_file,
)


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.document_repo = DocumentRepository(db)
        self.job_repo = JobRepository(db)

    async def upload_document(self, file: UploadFile):
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is missing."
            )

        if not is_allowed_file(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF and DOCX files are allowed."
            )

        ensure_directory(settings.UPLOAD_DIR)

        stored_filename = generate_stored_filename(file.filename)
        file_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

        content = await file.read()
        max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        if len(content) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB} MB."
            )

        with open(file_path, "wb") as f:
            f.write(content)

        document = self.document_repo.create(
            file_name=stored_filename,
            original_name=file.filename,
            file_type=get_file_extension(file.filename).replace(".", ""),
            file_path=file_path,
            status=DocumentStatus.UPLOADED,
            error_message=None,
        )

        self.job_repo.create(
            document_id=document.id,
            status=JobStatus.PENDING,
            error_message=None,
        )

        return document

    def get_document_status(self, document_id: UUID):
        document = self.document_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found."
            )
        return document
