from pathlib import Path

import pytest

from app.integrations.whisper.transcriber import WhisperTranscriber


def test_transcriber_rejects_missing_audio_file(tmp_path: Path) -> None:
    transcriber = WhisperTranscriber(
        model_name="small",
        model_cache_dir=tmp_path / "models",
    )

    with pytest.raises(FileNotFoundError, match="does not exist"):
        transcriber.transcribe(
            audio_path=tmp_path / "missing.mp3",
            language="pl",
        )
