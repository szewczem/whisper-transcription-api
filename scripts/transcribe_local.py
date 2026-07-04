import argparse
import json
from dataclasses import asdict
from pathlib import Path

from app.core.config import settings
from app.integrations.whisper.transcriber import WhisperTranscriber
from app.services.transcription.vtt_generator import build_webvtt


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe a local MP3 file with Whisper Small.")

    parser.add_argument(
        "audio_path",
        type=Path,
        help="Path to a local MP3 file.",
    )

    parser.add_argument(
        "--language",
        default="pl",
        help="Language code. Default: pl.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    settings.ensure_local_directories()

    audio_path = args.audio_path.expanduser().resolve()

    if audio_path.suffix.lower() != ".mp3":
        raise ValueError("Only MP3 files are supported in this local prototype.")

    transcriber = WhisperTranscriber(
        model_name=settings.whisper_model_name,
        model_cache_dir=settings.model_cache_dir,
    )

    result = transcriber.transcribe(
        audio_path=audio_path,
        language=args.language,
    )

    vtt_content = build_webvtt(result.segments)

    output_stem = settings.local_output_dir / audio_path.stem

    text_path = output_stem.with_suffix(".txt")
    vtt_path = output_stem.with_suffix(".vtt")
    json_path = output_stem.with_suffix(".json")

    text_path.write_text(result.text, encoding="utf-8")
    vtt_path.write_text(vtt_content, encoding="utf-8")

    json_payload = {
        "language": result.language,
        "text": result.text,
        "segments": [asdict(segment) for segment in result.segments],
    }

    json_path.write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Transcription completed.")
    print(f"Text file: {text_path}")
    print(f"VTT file:  {vtt_path}")
    print(f"JSON file: {json_path}")


if __name__ == "__main__":
    main()
