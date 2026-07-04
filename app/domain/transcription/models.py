from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TranscriptionSegment:
    start: float
    end: float
    text: str

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError("Segment start must be non-negative.")

        if self.end <= self.start:
            raise ValueError("Segment end must be greater than segment start.")


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    text: str
    language: str
    segments: tuple[TranscriptionSegment, ...]
