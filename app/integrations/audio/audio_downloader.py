from pathlib import Path

import httpx


class AudioDownloadError(RuntimeError):
    pass


def download_audio_file(
    *,
    audio_url: str,
    destination_path: Path,
    timeout_seconds: float = 60.0,
) -> None:
    try:
        with httpx.stream(
            "GET",
            audio_url,
            follow_redirects=True,
            timeout=timeout_seconds,
        ) as response:
            response.raise_for_status()

            with destination_path.open("wb") as file:
                for chunk in response.iter_bytes():
                    file.write(chunk)
    except httpx.HTTPError as error:
        raise AudioDownloadError(f"Failed to download audio file: {audio_url}") from error
