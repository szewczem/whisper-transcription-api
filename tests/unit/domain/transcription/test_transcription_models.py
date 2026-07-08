import pytest

from app.domain.transcription.models import TranscriptionSegment


def test_segment_rejects_negative_start_time() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        TranscriptionSegment(
            start=-0.1,
            end=1.0,
            text="Test",
        )


def test_segment_rejects_end_before_start() -> None:
    with pytest.raises(ValueError, match="greater than segment start"):
        TranscriptionSegment(
            start=2.0,
            end=1.0,
            text="Test",
        )
