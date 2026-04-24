from app.prompts.qa_prompt import build_qa_prompt
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService


class ChatService:
    def __init__(self, db):
        self.db = db
        self.retrieval = RetrievalService(db)
        self.llm = LLMService()

    def ask(self, question: str, document_ids=None, top_k=5):
        chunks = self.retrieval.retrieve(
            query=question,
            top_k=top_k,
            document_ids=document_ids,
        )

        if not chunks:
            return {
                "answer": "I couldn't find a reliable answer in the uploaded documents.",
                "citations": [],
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

        return {
            "answer": answer,
            "citations": citations,
        }
