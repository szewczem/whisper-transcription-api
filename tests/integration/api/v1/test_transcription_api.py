from collections.abc import Iterator
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.repositories.transcription_job_repository import TranscriptionJobRepository
from app.domain.transcription.job import TranscriptionJob, TranscriptionJobStatus


@pytest.fixture
def queue_delay_mock() -> Iterator[Mock]:
    with patch(
        "app.services.transcription.job_service.process_transcription_job.delay",
    ) as delay_mock:
        yield delay_mock


@pytest.mark.integration
def test_create_transcription_job_returns_accepted_and_persists_job(
    client: TestClient,
    db_session: Session,
    queue_delay_mock: Mock,
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

    queue_delay_mock.assert_called_once_with(str(job_id))


@pytest.mark.integration
def test_get_transcription_job_returns_queued_status(
    client: TestClient,
    db_session: Session,
    queue_delay_mock: Mock,
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
    assert "finished_at" not in body
    assert "completed_at" not in body

    queue_delay_mock.assert_called_once()


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


@pytest.mark.integration
def test_get_transcription_json_output_returns_completed_transcript(
    client: TestClient,
    db_session: Session,
) -> None:
    repository = TranscriptionJobRepository(db_session)

    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
        language="pl",
    )
    job.mark_processing()
    job.mark_completed(
        transcription="Dzień dobry świecie",
        vtt_content="WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nDzień dobry świecie\n",
    )

    repository.create(job)
    db_session.commit()

    response = client.get(f"/api/v1/transcribe/{job.id}/json")

    assert response.status_code == 200

    body = response.json()

    assert body["job_id"] == str(job.id)
    assert body["language"] == "pl"
    assert body["transcription"] == "Dzień dobry świecie"
    assert body["word_count"] == 3


@pytest.mark.integration
def test_get_transcription_txt_output_returns_plain_text(
    client: TestClient,
    db_session: Session,
) -> None:
    repository = TranscriptionJobRepository(db_session)

    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
        language="pl",
    )
    job.mark_processing()
    job.mark_completed(
        transcription="Dzień dobry świecie",
        vtt_content="WEBVTT\n",
    )

    repository.create(job)
    db_session.commit()

    response = client.get(f"/api/v1/transcribe/{job.id}/txt")

    assert response.status_code == 200
    assert response.text == "Dzień dobry świecie"
    assert response.headers["content-type"].startswith("text/plain")


@pytest.mark.integration
def test_get_transcription_vtt_output_returns_webvtt(
    client: TestClient,
    db_session: Session,
) -> None:
    repository = TranscriptionJobRepository(db_session)

    vtt_content = "WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nDzień dobry świecie\n"

    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
        language="pl",
    )
    job.mark_processing()
    job.mark_completed(
        transcription="Dzień dobry świecie",
        vtt_content=vtt_content,
    )

    repository.create(job)
    db_session.commit()

    response = client.get(f"/api/v1/transcribe/{job.id}/vtt")

    assert response.status_code == 200
    assert response.text == vtt_content
    assert response.headers["content-type"].startswith("text/vtt")


@pytest.mark.integration
def test_get_transcription_output_returns_conflict_when_job_is_not_completed(
    client: TestClient,
    db_session: Session,
) -> None:
    repository = TranscriptionJobRepository(db_session)

    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
        language="pl",
    )

    repository.create(job)
    db_session.commit()

    response = client.get(f"/api/v1/transcribe/{job.id}/txt")

    assert response.status_code == 409
    assert response.json()["detail"] == "Transcription job is not completed yet"


@pytest.mark.integration
def test_get_transcription_output_returns_not_found_for_unknown_job(
    client: TestClient,
) -> None:
    unknown_job_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/api/v1/transcribe/{unknown_job_id}/txt")

    assert response.status_code == 404
    assert response.json()["detail"] == "Transcription job not found"
