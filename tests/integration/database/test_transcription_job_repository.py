from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.database.repositories.transcription_job_repository import (
    TranscriptionJobRepository,
)
from app.domain.transcription.job import (
    TranscriptionJob,
    TranscriptionJobStatus,
)


@pytest.fixture
def repository(db_session: Session) -> TranscriptionJobRepository:
    return TranscriptionJobRepository(db_session)


@pytest.mark.integration
def test_repository_creates_and_retrieves_job(
    repository: TranscriptionJobRepository, db_session: Session
) -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
        webhook_url="https://example.com/webhook",
    )

    repository.create(job)
    db_session.commit()

    stored_job = repository.get_by_id(job.id)

    assert stored_job is not None
    assert stored_job.id == job.id
    assert stored_job.audio_url == "https://example.com/audio.mp3"
    assert stored_job.language == "pl"
    assert stored_job.webhook_url == "https://example.com/webhook"
    assert stored_job.status is TranscriptionJobStatus.QUEUED
    assert stored_job.progress == 0


@pytest.mark.integration
def test_repository_updates_job_processing_and_completion_state(
    repository: TranscriptionJobRepository, db_session: Session
) -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )

    repository.create(job)
    db_session.commit()

    job.mark_processing()
    job.update_progress(45)

    repository.update(job)
    db_session.commit()

    processing_job = repository.get_by_id(job.id)

    assert processing_job is not None
    assert processing_job.status is TranscriptionJobStatus.PROCESSING
    assert processing_job.progress == 45
    assert processing_job.started_at is not None

    job.mark_completed(
        transcription="Dzień dobry.",
        vtt_content="WEBVTT\n",
    )

    repository.update(job)
    db_session.commit()

    completed_job = repository.get_by_id(job.id)

    assert completed_job is not None
    assert completed_job.status is TranscriptionJobStatus.COMPLETED
    assert completed_job.progress == 100
    assert completed_job.transcription == "Dzień dobry."
    assert completed_job.vtt_content == "WEBVTT\n"
    assert completed_job.finished_at is not None


@pytest.mark.integration
def test_repository_returns_none_for_missing_job(repository: TranscriptionJobRepository) -> None:
    result = repository.get_by_id(uuid4())

    assert result is None


@pytest.mark.integration
def test_repository_rejects_update_for_missing_job(repository: TranscriptionJobRepository) -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/missing.mp3",
    )

    with pytest.raises(LookupError, match="does not exist"):
        repository.update(job)
