import json
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.prompts.qa_prompt import build_qa_prompt
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.retrieval = RetrievalService(db)
        self.llm = LLMService()
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)

    def ask(
        self,
        question: str,
        conversation_id: Optional[UUID] = None,
        document_ids=None,
        top_k: int = 5,
    ):
        conversation = self._get_or_create_conversation(conversation_id, question)

        recent_messages = self.message_repo.list_by_conversation(
            conversation_id=conversation.id,
            limit=6,
        )
        recent_messages = list(reversed(recent_messages))

        retrieval_query = self._build_retrieval_query(question, recent_messages)

        chunks = self.retrieval.retrieve(
            query=retrieval_query,
            top_k=top_k,
            document_ids=document_ids,
        )

        if not chunks:
            answer = "I couldn't find a reliable answer in the uploaded documents."
            citations = []

            self.message_repo.create(
                conversation_id=conversation.id,
                role="user",
                content=question,
            )
            self.message_repo.create(
                conversation_id=conversation.id,
                role="assistant",
                content=answer,
                retrieved_chunks=json.dumps(citations),
            )

            return {
                "conversation_id": conversation.id,
                "answer": answer,
                "citations": citations,
            }

        contexts = [c.text for c in chunks]
        prompt = build_qa_prompt(question, contexts)
        answer = self.llm.generate(prompt)
        refusal = "I couldn't find a reliable answer in the uploaded documents."

        if refusal in answer:
            answer = refusal

        citations = [
            {
                "chunk_id": str(c.chunk_id),
                "document_id": str(c.document_id),
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        self.message_repo.create(
            conversation_id=conversation.id,
            role="user",
            content=question,
        )
        self.message_repo.create(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            retrieved_chunks=json.dumps(citations),
        )

        return {
            "conversation_id": conversation.id,
            "answer": answer,
            "citations": citations,
        }

    def _get_or_create_conversation(
        self,
        conversation_id: Optional[UUID],
        question: str,
    ):
        if conversation_id:
            conversation = self.conversation_repo.get_by_id(conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found.",
                )
            return conversation

        title = question[:80]
        return self.conversation_repo.create(title=title)

    def _build_retrieval_query(self, question: str, recent_messages) -> str:
        if not recent_messages:
            return question

        previous_context = " ".join(
            message.content
            for message in recent_messages[-4:]
            if message.role == "user"
        )

        if not previous_context:
            return question

        return f"{previous_context}\n{question}"
