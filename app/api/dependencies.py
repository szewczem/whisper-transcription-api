from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.repositories.transcription_job_repository import (
    TranscriptionJobRepository,
)
from app.database.session import get_session
from app.services.transcription.job_service import TranscriptionJobService


def get_transcription_job_service(
    session: Session = Depends(get_session),
) -> TranscriptionJobService:
    repository = TranscriptionJobRepository(session)

    return TranscriptionJobService(
        repository=repository,
        session=session,
    )
