import pytest

from app.domain.transcription.models import TranscriptionSegment
from app.services.transcription.vtt_generator import (
    build_webvtt,
    format_vtt_timestamp,
)


def test_format_vtt_timestamp() -> None:
    assert format_vtt_timestamp(0) == "00:00:00.000"
    assert format_vtt_timestamp(3.25) == "00:00:03.250"
    assert format_vtt_timestamp(65.125) == "00:01:05.125"


def test_format_vtt_timestamp_rejects_negative_value() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        format_vtt_timestamp(-0.1)


def test_build_webvtt_sorts_segments_by_start_time() -> None:
    segments = (
        TranscriptionSegment(
            start=2.4,
            end=5.0,
            text="To jest drugi segment.",
        ),
        TranscriptionSegment(
            start=0.0,
            end=2.4,
            text="Dzień dobry.",
        ),
    )

    result = build_webvtt(segments)

    assert result == (
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:02.400\n"
        "Dzień dobry.\n\n"
        "00:00:02.400 --> 00:00:05.000\n"
        "To jest drugi segment.\n"
    )
