"""Transcription module using OpenAI Whisper."""
from pathlib import Path
import json

import whisper


def transcribe_video(video_path: str, model_size: str = "medium") -> dict:
    """Transcribe video with word-level timestamps."""
    model = whisper.load_model(model_size)
    result = model.transcribe(
        video_path,
        word_timestamps=True,
        verbose=False,
    )
    return result


def format_transcript_markdown(transcript: dict, title: str) -> str:
    """Convert transcript to readable markdown for blog embedding."""
    lines = [f"## {title}", ""]
    for segment in transcript.get("segments", []):
        text = segment.get("text", "").strip()
        if text:
            lines.append(text)
            lines.append("")
    return "\n".join(lines)


def save_transcript(transcript: dict, output_dir: Path, title: str) -> tuple[Path, Path]:
    """Save transcript as JSON and markdown."""
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "transcript.json"
    json_path.write_text(json.dumps(transcript, indent=2, ensure_ascii=False))
    md_path = output_dir / "transcript.md"
    md_path.write_text(format_transcript_markdown(transcript, title))
    return json_path, md_path
