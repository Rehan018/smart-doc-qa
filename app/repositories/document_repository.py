from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Document:
        document = Document(**kwargs)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_by_id(self, document_id: UUID) -> Optional[Document]:
        return (
            self.db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

    def list_by_ids(self, document_ids: List[UUID]) -> List[Document]:
        return (
            self.db.query(Document)
            .filter(Document.id.in_(document_ids))
            .all()
        )
