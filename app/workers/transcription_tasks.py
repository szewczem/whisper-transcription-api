import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.repositories.transcription_job_repository import (
    TranscriptionJobRepository,
)
from app.database.session import SessionFactory
from app.domain.transcription.job import TranscriptionJob, TranscriptionJobStatus
from app.integrations.audio.audio_downloader import download_audio_file
from app.integrations.webhook.client import WebhookDeliveryError, send_transcription_webhook
from app.integrations.whisper.transcriber import WhisperTranscriber
from app.services.transcription.metrics_logger import append_transcription_metrics
from app.services.transcription.vtt_generator import build_webvtt
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="transcriptions.process")
def process_transcription_job(job_id: str) -> None:
    parsed_job_id = UUID(job_id)

    with SessionFactory() as session:
        repository = TranscriptionJobRepository(session)
        job = repository.get_by_id(parsed_job_id)

        if job is None:
            return

        if job.status is not TranscriptionJobStatus.QUEUED:
            return

        try:
            job.mark_processing()
            repository.update(job)
            session.commit()

            with TemporaryDirectory() as temporary_directory:
                audio_path = Path(temporary_directory) / "audio.mp3"

                download_audio_file(
                    audio_url=job.audio_url,
                    destination_path=audio_path,
                )

                _update_job_progress(
                    repository=repository,
                    session=session,
                    job=job,
                    progress=30,
                )

                transcriber = WhisperTranscriber(
                    model_name=settings.whisper_model_name,
                    model_cache_dir=settings.model_cache_dir,
                )

                _update_job_progress(
                    repository=repository,
                    session=session,
                    job=job,
                    progress=45,
                )

                transcription_result = transcriber.transcribe(
                    audio_path=audio_path,
                    language=job.language,
                )

                _update_job_progress(
                    repository=repository,
                    session=session,
                    job=job,
                    progress=75,
                )

                vtt_content = build_webvtt(transcription_result.segments)

                _update_job_progress(
                    repository=repository,
                    session=session,
                    job=job,
                    progress=85,
                )

            job.mark_completed(
                transcription=transcription_result.text,
                vtt_content=vtt_content,
            )
            repository.update(job)
            session.commit()

            _append_metrics_safely(job)
            _send_webhook_safely(str(job.id))

        except Exception as error:
            session.rollback()

            failed_job = repository.get_by_id(parsed_job_id)
            if failed_job is None:
                raise

            failed_job.mark_failed(error=str(error))
            repository.update(failed_job)
            session.commit()

            _append_metrics_safely(failed_job)
            _send_webhook_safely(str(failed_job.id))

            raise


def _send_webhook_safely(job_id: str) -> None:
    with SessionFactory() as session:
        repository = TranscriptionJobRepository(session)
        job = repository.get_by_id(UUID(job_id))

        if job is None:
            return

        try:
            send_transcription_webhook(job=job)
        except WebhookDeliveryError as error:
            logger.warning("%s", error)


def _update_job_progress(
    *,
    repository: TranscriptionJobRepository,
    session: Session,
    job: TranscriptionJob,
    progress: int,
) -> None:
    job.update_progress(progress)
    repository.update(job)
    session.commit()


def _append_metrics_safely(job: TranscriptionJob) -> None:
    try:
        append_transcription_metrics(
            job=job,
            metrics_log_path=settings.metrics_log_path,
        )
    except Exception as error:
        logger.error(
            "Failed to write transcription metrics for job %s: %s",
            job.id,
            error,
        )