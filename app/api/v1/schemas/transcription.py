from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.domain.transcription.job import TranscriptionJobStatus


class CreateTranscriptionRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "audio_url": (
                        "https://static.prsa.pl/86623fd4-a991-43e2-841f-1f42e1ccb2bb.mp3"
                    ),
                    "language": "pl",
                    "webhook_url": "https://example.com/webhook",
                }
            ]
        },
    )

    audio_url: HttpUrl
    language: str = Field(
        default="pl",
        min_length=2,
        max_length=16,
    )
    webhook_url: HttpUrl | None = None


class CreateTranscriptionResponse(BaseModel):
    job_id: UUID
    status: TranscriptionJobStatus
    message: str


class TranscriptionStatusResponse(BaseModel):
    job_id: UUID
    status: TranscriptionJobStatus
    progress: int = Field(ge=0, le=100)

    transcription: str | None = None
    vtt_content: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    error: str | None = None
