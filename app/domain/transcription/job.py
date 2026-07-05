from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TranscriptionJobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class TranscriptionJob:
    audio_url: str
    language: str = "pl"
    webhook_url: str | None = None

    id: UUID = field(default_factory=uuid4)
    status: TranscriptionJobStatus = TranscriptionJobStatus.QUEUED
    progress: int = 0

    transcription: str | None = None
    vtt_content: str | None = None
    error: str | None = None

    created_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def mark_processing(self) -> None:
        if self.status is not TranscriptionJobStatus.QUEUED:
            raise ValueError("Only queued jobs can start processing.")

        self.status = TranscriptionJobStatus.PROCESSING
        self.started_at = utc_now()

    def update_progress(self, progress: int) -> None:
        if self.status is not TranscriptionJobStatus.PROCESSING:
            raise ValueError("Only processing jobs can update progress.")

        if not 0 <= progress < 100:
            raise ValueError("Progress must be between 0 and 99 while the job is processing.")

        if progress < self.progress:
            raise ValueError("Progress cannot decrease.")

        self.progress = progress

    def mark_completed(
        self,
        *,
        transcription: str,
        vtt_content: str,
    ) -> None:
        if self.status is not TranscriptionJobStatus.PROCESSING:
            raise ValueError("Only processing jobs can be completed.")

        self.status = TranscriptionJobStatus.COMPLETED
        self.progress = 100
        self.transcription = transcription
        self.vtt_content = vtt_content
        self.error = None
        self.finished_at = utc_now()

    def mark_failed(self, *, error: str) -> None:
        if self.status not in (
            TranscriptionJobStatus.QUEUED,
            TranscriptionJobStatus.PROCESSING,
        ):
            raise ValueError("Only queued or processing jobs can fail.")

        self.status = TranscriptionJobStatus.FAILED
        self.error = error
        self.finished_at = utc_now()
