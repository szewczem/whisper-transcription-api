from datetime import timezone
from uuid import UUID

import pytest

from app.domain.transcription.job import (
    TranscriptionJob,
    TranscriptionJobStatus,
)


def test_new_job_has_queued_status_and_default_values() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )

    assert isinstance(job.id, UUID)
    assert job.status is TranscriptionJobStatus.QUEUED
    assert job.progress == 0
    assert job.language == "pl"
    assert job.webhook_url is None
    assert job.created_at.tzinfo is timezone.utc


def test_job_can_start_processing() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )

    job.mark_processing()

    assert job.status is TranscriptionJobStatus.PROCESSING
    assert job.started_at is not None


def test_processing_job_can_update_progress() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )
    job.mark_processing()

    job.update_progress(45)

    assert job.progress == 45


def test_job_cannot_update_progress_before_processing() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )

    with pytest.raises(ValueError, match="processing"):
        job.update_progress(10)


def test_job_can_be_completed() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )
    job.mark_processing()
    job.update_progress(80)

    job.mark_completed(
        transcription="Dzień dobry.",
        vtt_content="WEBVTT\n",
    )

    assert job.status is TranscriptionJobStatus.COMPLETED
    assert job.progress == 100
    assert job.transcription == "Dzień dobry."
    assert job.vtt_content == "WEBVTT\n"
    assert job.error is None
    assert job.completed_at is not None


def test_job_can_fail() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )
    job.mark_processing()

    job.mark_failed(error="Unable to download audio file.")

    assert job.status is TranscriptionJobStatus.FAILED
    assert job.error == "Unable to download audio file."
    assert job.completed_at is not None
