import pytest
from sqlalchemy.orm import Session

from app.database.repositories.transcription_job_repository import (
    TranscriptionJobRepository,
)
from app.domain.transcription.job import TranscriptionJob, TranscriptionJobStatus
from app.workers.transcription_tasks import process_transcription_job


@pytest.mark.integration
def test_process_transcription_job_marks_job_as_processing(
    db_session: Session,
) -> None:
    repository = TranscriptionJobRepository(db_session)

    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )

    repository.create(job)
    db_session.commit()

    process_transcription_job(str(job.id))

    updated_job = repository.get_by_id(job.id)

    assert updated_job is not None
    assert updated_job.status is TranscriptionJobStatus.PROCESSING
    assert updated_job.progress == 0
    assert updated_job.started_at is not None
