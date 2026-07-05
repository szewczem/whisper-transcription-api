from uuid import UUID

from sqlalchemy.orm import Session

from app.database.models.transcription_job import TranscriptionJobRecord
from app.domain.transcription.job import (
    TranscriptionJob,
    TranscriptionJobStatus,
)


class TranscriptionJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, job: TranscriptionJob) -> TranscriptionJob:
        record = _to_record(job)

        self._session.add(record)
        self._session.flush()

        return _to_domain(record)

    def get_by_id(self, job_id: UUID) -> TranscriptionJob | None:
        record = self._session.get(TranscriptionJobRecord, job_id)

        if record is None:
            return None

        return _to_domain(record)

    def update(self, job: TranscriptionJob) -> TranscriptionJob:
        record = self._session.get(TranscriptionJobRecord, job.id)

        if record is None:
            raise LookupError(f"Transcription job does not exist: {job.id}")

        _apply_job_state(record, job)
        self._session.flush()

        return _to_domain(record)


def _to_record(job: TranscriptionJob) -> TranscriptionJobRecord:
    return TranscriptionJobRecord(
        id=job.id,
        audio_url=job.audio_url,
        language=job.language,
        webhook_url=job.webhook_url,
        status=job.status.value,
        progress=job.progress,
        transcription=job.transcription,
        vtt_content=job.vtt_content,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def _to_domain(record: TranscriptionJobRecord) -> TranscriptionJob:
    return TranscriptionJob(
        id=record.id,
        audio_url=record.audio_url,
        language=record.language,
        webhook_url=record.webhook_url,
        status=TranscriptionJobStatus(record.status),
        progress=record.progress,
        transcription=record.transcription,
        vtt_content=record.vtt_content,
        error=record.error,
        created_at=record.created_at,
        started_at=record.started_at,
        finished_at=record.finished_at,
    )


def _apply_job_state(record: TranscriptionJobRecord, job: TranscriptionJob) -> None:
    record.status = job.status.value
    record.progress = job.progress
    record.transcription = job.transcription
    record.vtt_content = job.vtt_content
    record.error = job.error
    record.started_at = job.started_at
    record.finished_at = job.finished_at
