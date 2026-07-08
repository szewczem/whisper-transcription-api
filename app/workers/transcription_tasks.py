from uuid import UUID

from app.database.repositories.transcription_job_repository import (
    TranscriptionJobRepository,
)
from app.database.session import SessionFactory
from app.domain.transcription.job import TranscriptionJobStatus
from app.workers.celery_app import celery_app


@celery_app.task(name="transcriptions.process")
def process_transcription_job(job_id: str) -> None:
    parsed_job_id = UUID(job_id)

    with SessionFactory() as session:
        repository = TranscriptionJobRepository(session)
        job = repository.get_by_id(parsed_job_id)

        if job is None:
            return

        if job.status is not TranscriptionJobStatus.QUEUED:
            return

        try:
            job.mark_processing()
            repository.update(job)
            session.commit()
        except Exception:
            session.rollback()
            raise
