from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[UUID] = None
    document_ids: Optional[List[UUID]] = None
    top_k: int = 5


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int


class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: str
    citations: List[Citation]
