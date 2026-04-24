from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.message import Message


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        retrieved_chunks: str | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            retrieved_chunks=retrieved_chunks,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def list_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 10,
    ) -> List[Message]:
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
