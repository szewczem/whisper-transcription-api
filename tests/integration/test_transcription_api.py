from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.repositories.transcription_job_repository import (
    TranscriptionJobRepository,
)
from app.domain.transcription.job import TranscriptionJobStatus


@pytest.mark.integration
def test_create_transcription_job_returns_accepted_and_persists_job(
    client: TestClient, db_session: Session
) -> None:
    response = client.post(
        "/api/v1/transcribe",
        json={
            "audio_url": "https://example.com/audio.mp3",
            "language": "pl",
            "webhook_url": "https://example.com/webhook",
        },
    )

    assert response.status_code == 202

    body = response.json()

    assert body["status"] == "queued"
    assert body["message"] == "Transcription job created successfully"

    job_id = UUID(body["job_id"])

    repository = TranscriptionJobRepository(db_session)
    stored_job = repository.get_by_id(job_id)

    assert stored_job is not None
    assert stored_job.status is TranscriptionJobStatus.QUEUED
    assert stored_job.audio_url == "https://example.com/audio.mp3"
    assert stored_job.language == "pl"
    assert stored_job.webhook_url == "https://example.com/webhook"


@pytest.mark.integration
def test_get_transcription_job_returns_queued_status(
    client: TestClient, db_session: Session
) -> None:
    create_response = client.post(
        "/api/v1/transcribe",
        json={
            "audio_url": "https://example.com/audio.mp3",
        },
    )

    job_id = create_response.json()["job_id"]

    response = client.get(
        f"/api/v1/transcribe/{job_id}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["job_id"] == job_id
    assert body["status"] == "queued"
    assert body["progress"] == 0
    assert "transcription" not in body
    assert "vtt_content" not in body
    assert "completed_at" not in body


@pytest.mark.integration
def test_get_transcription_job_returns_404_for_unknown_job(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/transcribe/{uuid4()}",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Transcription job not found.",
    }


@pytest.mark.integration
def test_create_transcription_job_rejects_invalid_audio_url(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transcribe",
        json={
            "audio_url": "not-a-valid-url",
        },
    )

    assert response.status_code == 422
