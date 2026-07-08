from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from app.core.config import settings
from app.database.repositories.transcription_job_repository import (
    TranscriptionJobRepository,
)
from app.database.session import SessionFactory
from app.domain.transcription.job import TranscriptionJobStatus
from app.integrations.audio.audio_downloader import download_audio_file
from app.integrations.whisper.transcriber import WhisperTranscriber
from app.services.transcription.metrics_logger import append_transcription_metrics
from app.services.transcription.vtt_generator import build_webvtt
from app.workers.celery_app import celery_app


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

                transcriber = WhisperTranscriber(
                    model_name=settings.whisper_model_name,
                    model_cache_dir=settings.model_cache_dir,
                )

                transcription_result = transcriber.transcribe(
                    audio_path=audio_path,
                    language=job.language,
                )

                vtt_content = build_webvtt(transcription_result.segments)

            job.mark_completed(
                transcription=transcription_result.text,
                vtt_content=vtt_content,
            )
            repository.update(job)
            session.commit()

            append_transcription_metrics(
                job=job,
                metrics_log_path=settings.metrics_log_path,
            )

        except Exception as error:
            session.rollback()

            failed_job = repository.get_by_id(parsed_job_id)
            if failed_job is None:
                raise

            failed_job.mark_failed(error=str(error))
            repository.update(failed_job)
            session.commit()

            append_transcription_metrics(
                job=failed_job,
                metrics_log_path=settings.metrics_log_path,
            )

            raise
