"""Tests for transcription module."""
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.transcribe import transcribe_video, format_transcript_markdown


def test_transcribe_video_returns_word_segments():
    mock_result = {
        "text": "This play breaks every zone.",
        "segments": [
            {
                "start": 0.0, "end": 2.5,
                "text": "This play breaks every zone.",
                "words": [
                    {"word": "This", "start": 0.0, "end": 0.3},
                    {"word": "play", "start": 0.3, "end": 0.6},
                    {"word": "breaks", "start": 0.6, "end": 1.0},
                    {"word": "every", "start": 1.0, "end": 1.3},
                    {"word": "zone.", "start": 1.3, "end": 1.8},
                ]
            }
        ]
    }
    mock_model = MagicMock()
    mock_model.transcribe.return_value = mock_result
    with patch("src.transcribe.whisper.load_model", return_value=mock_model):
        result = transcribe_video("fake_video.mp4", model_size="base")
    assert "segments" in result
    assert len(result["segments"]) == 1
    assert len(result["segments"][0]["words"]) == 5


def test_format_transcript_markdown():
    transcript = {
        "text": "This play breaks every zone. Run it against man defense too.",
        "segments": [
            {"start": 0.0, "end": 2.5, "text": "This play breaks every zone."},
            {"start": 2.5, "end": 5.0, "text": "Run it against man defense too."},
        ]
    }
    md = format_transcript_markdown(transcript, title="Chin Entry")
    assert "## Chin Entry" in md
    assert "This play breaks every zone." in md
    assert "Run it against man defense too." in md
