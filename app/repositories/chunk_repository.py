from typing import List
from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk


class ChunkRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_create(self, chunks: List[Chunk]):
        self.db.add_all(chunks)
        self.db.commit()