from sqlalchemy.orm import Session

from app.db.models.job import Job


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Job:
        job = Job(**kwargs)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job