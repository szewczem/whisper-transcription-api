import json
from pathlib import Path

from app.domain.transcription.job import TranscriptionJob
from app.services.transcription.metrics_logger import (
    append_transcription_metrics,
    calculate_processing_time_seconds,
    count_words,
)


def test_count_words_returns_zero_for_missing_text() -> None:
    assert count_words(None) == 0


def test_count_words_counts_words_in_text() -> None:
    assert count_words("Dzień dobry świecie") == 3


def test_calculate_processing_time_seconds_returns_none_for_unfinished_job() -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
    )

    assert calculate_processing_time_seconds(job) is None


def test_append_transcription_metrics_writes_json_line(tmp_path: Path) -> None:
    job = TranscriptionJob(
        audio_url="https://example.com/audio.mp3",
        language="pl",
    )
    job.mark_processing()
    job.mark_completed(
        transcription="Dzień dobry świecie",
        vtt_content="WEBVTT\n",
    )

    metrics_log_path = tmp_path / "transcription_metrics.log"

    append_transcription_metrics(
        job=job,
        metrics_log_path=metrics_log_path,
    )

    lines = metrics_log_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 1

    payload = json.loads(lines[0])

    assert payload["job_id"] == str(job.id)
    assert payload["audio_url"] == "https://example.com/audio.mp3"
    assert payload["language"] == "pl"
    assert payload["word_count"] == 3
    assert payload["status"] == "completed"
    assert payload["error"] is None
    assert payload["processing_time"] is not None
