from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "whisper_transcription_api",
    broker=settings.celery_broker_url,
    include=["app.workers.transcription_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_ignore_result=True,
)
