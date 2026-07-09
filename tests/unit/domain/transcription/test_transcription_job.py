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
    assert job.transcription is None
    assert job.vtt_content is None
    assert job.error is None
    assert job.started_at is None
    assert job.finished_at is None
    assert job.created_at.tzinfo is timezone.utc


def test_job_can_start_processing() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )

    job.mark_processing()

    assert job.status is TranscriptionJobStatus.PROCESSING
    assert job.progress == 10
    assert job.started_at is not None


def test_job_cannot_start_processing_twice() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )
    job.mark_processing()

    with pytest.raises(ValueError, match="Only queued jobs can start processing"):
        job.mark_processing()


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

    with pytest.raises(ValueError, match="Only processing jobs can update progress"):
        job.update_progress(10)


@pytest.mark.parametrize("progress", [-1, 100, 101])
def test_processing_job_rejects_invalid_progress_values(progress: int) -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )
    job.mark_processing()

    with pytest.raises(ValueError, match="Progress must be between 0 and 99"):
        job.update_progress(progress)


def test_processing_job_cannot_decrease_progress() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )
    job.mark_processing()
    job.update_progress(45)

    with pytest.raises(ValueError, match="Progress cannot decrease"):
        job.update_progress(30)


def test_job_can_be_completed() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )
    job.mark_processing()
    job.update_progress(85)

    job.mark_completed(
        transcription="Dzień dobry.",
        vtt_content="WEBVTT\n",
    )

    assert job.status is TranscriptionJobStatus.COMPLETED
    assert job.progress == 100
    assert job.transcription == "Dzień dobry."
    assert job.vtt_content == "WEBVTT\n"
    assert job.error is None
    assert job.finished_at is not None


def test_queued_job_can_fail() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )

    job.mark_failed(error="Unable to download audio file.")

    assert job.status is TranscriptionJobStatus.FAILED
    assert job.progress == 0
    assert job.error == "Unable to download audio file."
    assert job.finished_at is not None


def test_processing_job_can_fail_and_keep_last_progress() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )
    job.mark_processing()
    job.update_progress(45)

    job.mark_failed(error="Unable to transcribe audio file.")

    assert job.status is TranscriptionJobStatus.FAILED
    assert job.progress == 45
    assert job.error == "Unable to transcribe audio file."
    assert job.finished_at is not None


def test_completed_job_cannot_fail() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )
    job.mark_processing()
    job.mark_completed(
        transcription="Dzień dobry.",
        vtt_content="WEBVTT\n",
    )

    with pytest.raises(ValueError, match="Only queued or processing jobs can fail"):
        job.mark_failed(error="Unexpected error.")
