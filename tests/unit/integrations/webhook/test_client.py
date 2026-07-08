from unittest.mock import Mock, patch

import httpx
import pytest

from app.domain.transcription.job import TranscriptionJob
from app.integrations.webhook.client import (
    WebhookDeliveryError,
    send_transcription_webhook,
)


def test_send_transcription_webhook_does_nothing_without_webhook_url() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )

    with patch("app.integrations.webhook.client.httpx.post") as post_mock:
        send_transcription_webhook(job=job)

    post_mock.assert_not_called()


def test_send_transcription_webhook_posts_completed_job_payload() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
        language="pl",
        webhook_url="https://example.com/webhook",
    )
    job.mark_processing()
    job.mark_completed(
        transcription="Dzień dobry.",
        vtt_content="WEBVTT\n",
    )

    response_mock = Mock()
    response_mock.raise_for_status.return_value = None

    with patch(
        "app.integrations.webhook.client.httpx.post",
        return_value=response_mock,
    ) as post_mock:
        send_transcription_webhook(job=job)

    post_mock.assert_called_once()

    _, kwargs = post_mock.call_args

    assert kwargs["timeout"] == 10.0

    payload = kwargs["json"]

    assert payload["job_id"] == str(job.id)
    assert payload["status"] == "completed"
    assert payload["progress"] == 100
    assert payload["audio_url"] == "https://example.com/audio.mp3"
    assert payload["language"] == "pl"
    assert payload["transcription"] == "Dzień dobry."
    assert payload["vtt_content"] == "WEBVTT\n"
    assert payload["created_at"] is not None
    assert payload["error"] is None


def test_send_transcription_webhook_posts_failed_job_payload() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
        language="pl",
        webhook_url="https://example.com/webhook",
    )
    job.mark_processing()
    job.mark_failed(error="download failed")

    response_mock = Mock()
    response_mock.raise_for_status.return_value = None

    with patch(
        "app.integrations.webhook.client.httpx.post",
        return_value=response_mock,
    ) as post_mock:
        send_transcription_webhook(job=job)

    post_mock.assert_called_once()

    _, kwargs = post_mock.call_args
    payload = kwargs["json"]

    assert payload["job_id"] == str(job.id)
    assert payload["status"] == "failed"
    assert payload["audio_url"] == "https://example.com/audio.mp3"
    assert payload["language"] == "pl"
    assert payload["transcription"] is None
    assert payload["vtt_content"] is None
    assert payload["error"] == "download failed"


def test_send_transcription_webhook_raises_delivery_error_on_http_error() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
        webhook_url="https://example.com/webhook",
    )
    job.mark_processing()
    job.mark_completed(
        transcription="Dzień dobry.",
        vtt_content="WEBVTT\n",
    )

    with patch(
        "app.integrations.webhook.client.httpx.post",
        side_effect=httpx.RequestError("connection failed"),
    ):
        with pytest.raises(WebhookDeliveryError, match="Failed to deliver webhook"):
            send_transcription_webhook(job=job)
