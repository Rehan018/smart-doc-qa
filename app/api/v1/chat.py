from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.services.retrieval_service import RetrievalService

router = APIRouter()


class RetrievalRequest(BaseModel):
    query: str
    document_ids: Optional[List[UUID]] = None
    top_k: int = 5


@router.post("/retrieve")
def retrieve_chunks(
    request: RetrievalRequest,
    db: Session = Depends(get_db),
):
    service = RetrievalService(db)

    chunks = service.retrieve(
        query=request.query,
        top_k=request.top_k,
        document_ids=request.document_ids,
    )

    return {
        "count": len(chunks),
        "chunks": [
            {
                "chunk_id": str(c.chunk_id),
                "document_id": str(c.document_id),
                "chunk_index": c.chunk_index,
                "text": c.text[:200],
            }
            for c in chunks
        ]
    }


@router.post("/ask", response_model=ChatResponse)
def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    service = ChatService(db)

    return service.ask(
        question=request.question,
        document_ids=request.document_ids,
        top_k=request.top_k,
    )
