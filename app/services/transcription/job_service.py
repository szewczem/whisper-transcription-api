from uuid import UUID

from sqlalchemy.orm import Session

from app.database.repositories.transcription_job_repository import (
    TranscriptionJobRepository,
)
from app.domain.transcription.job import TranscriptionJob
from app.workers.transcription_tasks import process_transcription_job


class TranscriptionJobService:
    def __init__(
        self,
        *,
        repository: TranscriptionJobRepository,
        session: Session,
    ) -> None:
        self._repository = repository
        self._session = session

    def create_job(
        self,
        *,
        audio_url: str,
        language: str,
        webhook_url: str | None,
    ) -> TranscriptionJob:
        job = TranscriptionJob(
            audio_url=audio_url,
            language=language,
            webhook_url=webhook_url,
        )

        try:
            stored_job = self._repository.create(job)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

        process_transcription_job.delay(str(stored_job.id))

        return stored_job

    def get_job(self, job_id: UUID) -> TranscriptionJob | None:
        return self._repository.get_by_id(job_id)
