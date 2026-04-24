import json
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.constants import NO_ANSWER_MESSAGE
from app.db.models.document import DocumentStatus
from app.prompts.qa_prompt import build_qa_prompt
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
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
        self.document_repo = DocumentRepository(db)

    def ask(
        self,
        question: str,
        conversation_id: Optional[UUID] = None,
        document_ids=None,
        top_k: int = 5,
    ):
        if not question or not question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty.",
            )

        self._validate_documents_ready(document_ids)

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
            return self._save_and_return(
                conversation_id=conversation.id,
                question=question,
                answer=NO_ANSWER_MESSAGE,
                citations=[],
            )

        contexts = [c.text for c in chunks]
        prompt = build_qa_prompt(question, contexts)
        try:
            answer = self.llm.generate(prompt)
        except Exception:
            answer = "The answer service is temporarily unavailable. Please try again later."
            return self._save_and_return(
                conversation_id=conversation.id,
                question=question,
                answer=answer,
                citations=[],
            )

        if not answer or not answer.strip():
            answer = NO_ANSWER_MESSAGE

        if NO_ANSWER_MESSAGE in answer:
            answer = NO_ANSWER_MESSAGE

        citations = [
            {
                "chunk_id": str(c.chunk_id),
                "document_id": str(c.document_id),
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        return self._save_and_return(
            conversation_id=conversation.id,
            question=question,
            answer=answer,
            citations=citations,
        )

    def _validate_documents_ready(self, document_ids):
        if not document_ids:
            return

        documents = self.document_repo.list_by_ids(document_ids)
        found_ids = {str(doc.id) for doc in documents}
        requested_ids = {str(doc_id) for doc_id in document_ids}

        missing_ids = requested_ids - found_ids
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document(s) not found: {', '.join(missing_ids)}",
            )

        not_ready = [
            doc for doc in documents
            if doc.status != DocumentStatus.READY
        ]

        if not_ready:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="One or more selected documents are not ready for Q&A yet.",
            )

    def _save_and_return(self, conversation_id, question, answer, citations):
        self.message_repo.create(
            conversation_id=conversation_id,
            role="user",
            content=question,
        )
        self.message_repo.create(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            retrieved_chunks=json.dumps(citations),
        )

        return {
            "conversation_id": conversation_id,
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
