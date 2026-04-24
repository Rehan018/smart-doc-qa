from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService


class RetrievedChunk:
    def __init__(self, chunk_id, text, document_id, chunk_index, distance: float):
        self.chunk_id = chunk_id
        self.text = text
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.distance = distance


class RetrievalService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[UUID]] = None,
        max_distance: float = 1.5,
    ) -> List[RetrievedChunk]:
        query_embedding = self.embedding_service.embed_texts([query])
        vector_service = VectorService(dim=query_embedding.shape[1])
        results = vector_service.search(query_embedding, top_k=top_k)

        if not results:
            return []

        filtered_results = [
            result for result in results
            if result.distance <= max_distance
        ]

        if not filtered_results:
            return []

        chunk_ids = [result.chunk_id for result in filtered_results]

        chunks = (
            self.db.query(Chunk)
            .filter(Chunk.id.in_(chunk_ids))
            .all()
        )

        if document_ids:
            document_id_set = {str(doc_id) for doc_id in document_ids}
            chunks = [
                c for c in chunks
                if str(c.document_id) in document_id_set
            ]

        chunk_map = {str(c.id): c for c in chunks}
        distance_map = {r.chunk_id: r.distance for r in filtered_results}

        ordered_chunks = []
        for cid in chunk_ids:
            if cid in chunk_map:
                c = chunk_map[cid]
                ordered_chunks.append(
                    RetrievedChunk(
                        chunk_id=c.id,
                        text=c.text,
                        document_id=c.document_id,
                        chunk_index=c.chunk_index,
                        distance=distance_map[cid],
                    )
                )

        return ordered_chunks
