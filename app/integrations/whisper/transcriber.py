from pathlib import Path
from typing import Any

import whisper

from app.domain.transcription.models import (
    TranscriptionResult,
    TranscriptionSegment,
)


class WhisperTranscriber:
    def __init__(
        self,
        *,
        model_name: str,
        model_cache_dir: Path,
    ) -> None:
        self._model_name = model_name
        self._model_cache_dir = model_cache_dir
        self._model: Any | None = None

    def transcribe(
        self,
        *,
        audio_path: Path,
        language: str,
    ) -> TranscriptionResult:
        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio file does not exist: {audio_path}")

        raw_result = self._get_model().transcribe(
            str(audio_path),
            language=language,
            task="transcribe",
            fp16=False,
            verbose=False,
        )

        segments = tuple(
            TranscriptionSegment(
                start=float(segment["start"]),
                end=float(segment["end"]),
                text=str(segment["text"]).strip(),
            )
            for segment in raw_result["segments"]
        )

        return TranscriptionResult(
            text=str(raw_result["text"]).strip(),
            language=language,
            segments=segments,
        )

    def _get_model(self) -> Any:
        if self._model is None:
            self._model = whisper.load_model(
                self._model_name,
                download_root=str(self._model_cache_dir),
            )

        return self._model
