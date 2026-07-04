from collections.abc import Sequence

from app.domain.transcription.models import TranscriptionSegment


def format_vtt_timestamp(total_seconds: float) -> str:
    if total_seconds < 0:
        raise ValueError("Timestamp cannot be negative.")

    total_milliseconds = round(total_seconds * 1000)

    hours, remainder = divmod(total_milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def build_webvtt(segments: Sequence[TranscriptionSegment]) -> str:
    blocks = ["WEBVTT"]

    for segment in sorted(segments, key=lambda item: item.start):
        text = " ".join(segment.text.split())

        if not text:
            continue

        start = format_vtt_timestamp(segment.start)
        end = format_vtt_timestamp(segment.end)

        blocks.append(f"{start} --> {end}\n{text}")

    return "\n\n".join(blocks) + "\n"
