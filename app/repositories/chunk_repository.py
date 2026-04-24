from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk


class ChunkRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_create(self, chunks: List[Chunk]):
        self.db.add_all(chunks)
        self.db.commit()

    def delete_by_document_id(self, document_id: UUID):
        (
            self.db.query(Chunk)
            .filter(Chunk.document_id == document_id)
            .delete()
        )
        self.db.commit()
