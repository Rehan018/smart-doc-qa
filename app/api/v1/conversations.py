from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationResponse,
)

router = APIRouter()


@router.post("/", response_model=ConversationResponse)
def create_conversation(
    request: ConversationCreateRequest,
    db: Session = Depends(get_db),
):
    repo = ConversationRepository(db)
    return repo.create(title=request.title)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)

    conversation = conversation_repo.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    messages = message_repo.list_by_conversation(conversation_id, limit=50)
    messages = list(reversed(messages))

    return {
        "conversation": conversation,
        "messages": messages,
    }
