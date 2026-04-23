import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))

    role = Column(String, nullable=False)  # user / assistant
    content = Column(Text, nullable=False)

    retrieved_chunks = Column(Text, nullable=True)  # store JSON string

    created_at = Column(DateTime(timezone=True), server_default=func.now())