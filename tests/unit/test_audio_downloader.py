from pathlib import Path

import pytest

from app.integrations.audio_downloader import AudioDownloadError, download_audio_file


def test_download_audio_file_raises_error_for_unreachable_url(tmp_path: Path) -> None:
    destination_path = tmp_path / "audio.mp3"

    with pytest.raises(AudioDownloadError):
        download_audio_file(
            audio_url="http://127.0.0.1:1/audio.mp3",
            destination_path=destination_path,
            timeout_seconds=0.1,
        )
