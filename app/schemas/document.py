from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: UUID
    file_name: str
    original_name: str
    file_type: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    id: UUID
    file_name: str
    original_name: str
    file_type: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True