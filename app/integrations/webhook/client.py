from datetime import datetime
from typing import Any

import httpx

from app.domain.transcription.job import TranscriptionJob


class WebhookDeliveryError(RuntimeError):
    pass


def send_transcription_webhook(
    *,
    job: TranscriptionJob,
    timeout_seconds: float = 10.0,
) -> None:
    if job.webhook_url is None:
        return

    payload = _build_webhook_payload(job)

    try:
        response = httpx.post(
            job.webhook_url,
            json=payload,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise WebhookDeliveryError(
            f"Failed to deliver webhook for transcription job {job.id}"
        ) from error


def _build_webhook_payload(job: TranscriptionJob) -> dict[str, Any]:
    return {
        "job_id": str(job.id),
        "status": job.status.value,
        "progress": job.progress,
        "audio_url": job.audio_url,
        "language": job.language,
        "transcription": job.transcription,
        "vtt_content": job.vtt_content,
        "created_at": _serialize_datetime(job.created_at),
        "completed_at": _serialize_datetime(job.finished_at),
        "error": job.error,
    }


def _serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None

    return value.isoformat()
