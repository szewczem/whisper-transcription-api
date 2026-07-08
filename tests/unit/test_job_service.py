from unittest.mock import Mock, patch

from app.domain.transcription.job import TranscriptionJob
from app.services.transcription.job_service import TranscriptionJobService


class FakeRepository:
    def __init__(self) -> None:
        self.created_job: TranscriptionJob | None = None

    def create(self, job: TranscriptionJob) -> TranscriptionJob:
        self.created_job = job
        return job

    def get_by_id(self, job_id):
        return None


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_create_job_saves_job_and_queues_celery_task() -> None:
    repository = FakeRepository()
    session = FakeSession()

    service = TranscriptionJobService(
        repository=repository,  # type: ignore[arg-type]
        session=session,  # type: ignore[arg-type]
    )

    with patch(
        "app.workers.transcription_tasks.process_transcription_job.delay",
        Mock(),
    ) as delay_mock:
        job = service.create_job(
            audio_url="https://example.com/audio.mp3",
            language="pl",
            webhook_url=None,
        )

    assert repository.created_job is not None
    assert session.committed is True
    assert session.rolled_back is False
    delay_mock.assert_called_once_with(str(job.id))
