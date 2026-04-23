from typing import List, Optional
from uuid import UUID

import numpy as np
from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService


class RetrievedChunk:
    def __init__(self, chunk_id, text, document_id, chunk_index):
        self.chunk_id = chunk_id
        self.text = text
        self.document_id = document_id
        self.chunk_index = chunk_index


class RetrievalService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[RetrievedChunk]:
        # 1. embed query
        query_embedding = self.embedding_service.embed_texts([query])

        # 2. load vector index
        vector_service = VectorService(dim=query_embedding.shape[1])

        # 3. search FAISS
        chunk_ids = vector_service.search(query_embedding, top_k=top_k)

        if not chunk_ids:
            return []

        # 4. fetch chunks from DB
        chunks = (
            self.db.query(Chunk)
            .filter(Chunk.id.in_(chunk_ids))
            .all()
        )

        # 5. optional filtering by document_ids
        if document_ids:
            chunks = [
                c for c in chunks
                if c.document_id in document_ids
            ]

        # 6. preserve order from FAISS result
        chunk_map = {str(c.id): c for c in chunks}

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
                    )
                )

        return ordered_chunks
