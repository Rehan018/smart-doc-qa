import time
from datetime import datetime, timezone
from uuid import UUID

from app.db.models.document import Document, DocumentStatus
from app.db.models.job import Job, JobStatus
from app.db.session import SessionLocal
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.process_document")
def process_document(document_id: str):
    db = SessionLocal()
    try:
        doc_uuid = UUID(document_id)

        document = db.query(Document).filter(Document.id == doc_uuid).first()
        if not document:
            return {"error": "Document not found"}

        job = (
            db.query(Job)
            .filter(Job.document_id == doc_uuid)
            .order_by(Job.id.desc())
            .first()
        )

        if not job:
            return {"error": "Job not found"}

        document.status = DocumentStatus.PROCESSING
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        time.sleep(3)

        document.status = DocumentStatus.READY
        document.error_message = None

        job.status = JobStatus.SUCCESS
        job.error_message = None
        job.completed_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "document_id": str(document.id),
            "document_status": document.status,
            "job_status": job.status,
        }

    except Exception as exc:
        db.rollback()

        try:
            doc_uuid = UUID(document_id)
            document = db.query(Document).filter(Document.id == doc_uuid).first()
            job = (
                db.query(Job)
                .filter(Job.document_id == doc_uuid)
                .order_by(Job.id.desc())
                .first()
            )

            if document:
                document.status = DocumentStatus.FAILED
                document.error_message = str(exc)

            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)

            db.commit()
        except Exception:
            db.rollback()

        raise
    finally:
        db.close()
