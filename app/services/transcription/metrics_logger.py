import json
from datetime import datetime, timezone
from pathlib import Path

from app.domain.transcription.job import TranscriptionJob


def count_words(text: str | None) -> int:
    if text is None:
        return 0

    return len(text.split())


def calculate_processing_time_seconds(job: TranscriptionJob) -> float | None:
    if job.started_at is None or job.finished_at is None:
        return None

    return round(
        (job.finished_at - job.started_at).total_seconds(),
        3,
    )


def append_transcription_metrics(
    *,
    job: TranscriptionJob,
    metrics_log_path: Path,
) -> None:
    metrics_log_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "job_id": str(job.id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processing_time": calculate_processing_time_seconds(job),
        "audio_url": job.audio_url,
        "language": job.language,
        "word_count": count_words(job.transcription),
        "status": job.status.value,
        "error": job.error,
    }

    with metrics_log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")
