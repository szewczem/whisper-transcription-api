from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.database.repositories.transcription_job_repository import (
    TranscriptionJobRepository,
)
from app.domain.transcription.job import TranscriptionJob, TranscriptionJobStatus
from app.domain.transcription.models import TranscriptionResult, TranscriptionSegment
from app.integrations.webhook.client import WebhookDeliveryError
from app.workers.transcription_tasks import process_transcription_job


@pytest.mark.integration
def test_process_transcription_job_completes_job(
    db_session: Session,
) -> None:
    repository = TranscriptionJobRepository(db_session)

    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
        webhook_url="https://example.com/webhook",
    )

    repository.create(job)
    db_session.commit()

    fake_result = TranscriptionResult(
        text="Dzień dobry.",
        language="pl",
        segments=(
            TranscriptionSegment(
                start=0.0,
                end=1.5,
                text="Dzień dobry.",
            ),
        ),
    )

    with (
        patch("app.workers.transcription_tasks.download_audio_file") as download_mock,
        patch(
            "app.workers.transcription_tasks.WhisperTranscriber",
        ) as transcriber_class_mock,
        patch(
            "app.workers.transcription_tasks.append_transcription_metrics",
        ) as metrics_mock,
        patch(
            "app.workers.transcription_tasks.send_transcription_webhook",
        ) as webhook_mock,
    ):
        transcriber_mock = Mock()
        transcriber_mock.transcribe.return_value = fake_result
        transcriber_class_mock.return_value = transcriber_mock

        process_transcription_job(str(job.id))

    updated_job = repository.get_by_id(job.id)

    assert updated_job is not None
    assert updated_job.status is TranscriptionJobStatus.COMPLETED
    assert updated_job.progress == 100
    assert updated_job.transcription == "Dzień dobry."
    assert updated_job.vtt_content is not None
    assert "WEBVTT" in updated_job.vtt_content
    assert updated_job.error is None
    assert updated_job.started_at is not None
    assert updated_job.finished_at is not None

    download_mock.assert_called_once()
    transcriber_mock.transcribe.assert_called_once()
    metrics_mock.assert_called_once()
    webhook_mock.assert_called_once()


@pytest.mark.integration
def test_process_transcription_job_marks_job_as_failed_on_error(
    db_session: Session,
) -> None:
    repository = TranscriptionJobRepository(db_session)

    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
        webhook_url="https://example.com/webhook",
    )

    repository.create(job)
    db_session.commit()

    with (
        patch(
            "app.workers.transcription_tasks.download_audio_file",
            side_effect=RuntimeError("download failed"),
        ),
        patch(
            "app.workers.transcription_tasks.append_transcription_metrics",
        ) as metrics_mock,
        patch(
            "app.workers.transcription_tasks.send_transcription_webhook",
        ) as webhook_mock,
    ):
        with pytest.raises(RuntimeError, match="download failed"):
            process_transcription_job(str(job.id))

    updated_job = repository.get_by_id(job.id)

    assert updated_job is not None
    assert updated_job.status is TranscriptionJobStatus.FAILED
    assert updated_job.error == "download failed"
    assert updated_job.finished_at is not None

    metrics_mock.assert_called_once()
    webhook_mock.assert_called_once()


@pytest.mark.integration
def test_process_transcription_job_keeps_completed_status_when_webhook_fails(
    db_session: Session,
) -> None:
    repository = TranscriptionJobRepository(db_session)

    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
        webhook_url="https://example.com/webhook",
    )

    repository.create(job)
    db_session.commit()

    fake_result = TranscriptionResult(
        text="Dzień dobry.",
        language="pl",
        segments=(
            TranscriptionSegment(
                start=0.0,
                end=1.5,
                text="Dzień dobry.",
            ),
        ),
    )

    with (
        patch("app.workers.transcription_tasks.download_audio_file"),
        patch(
            "app.workers.transcription_tasks.WhisperTranscriber",
        ) as transcriber_class_mock,
        patch("app.workers.transcription_tasks.append_transcription_metrics"),
        patch(
            "app.workers.transcription_tasks.send_transcription_webhook",
            side_effect=WebhookDeliveryError("webhook failed"),
        ) as webhook_mock,
    ):
        transcriber_mock = Mock()
        transcriber_mock.transcribe.return_value = fake_result
        transcriber_class_mock.return_value = transcriber_mock

        process_transcription_job(str(job.id))

    updated_job = repository.get_by_id(job.id)

    assert updated_job is not None
    assert updated_job.status is TranscriptionJobStatus.COMPLETED
    assert updated_job.progress == 100
    assert updated_job.transcription == "Dzień dobry."
    assert updated_job.error is None

    webhook_mock.assert_called_once()
