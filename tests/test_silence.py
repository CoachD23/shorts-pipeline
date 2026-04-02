"""Tests for auto-silence removal."""
from src.silence import build_speech_segments, build_trim_filter


def test_build_speech_segments_with_silences():
    silences = [
        {"start": 2.0, "end": 3.5},
        {"start": 6.0, "end": 7.0},
    ]
    segments = build_speech_segments(silences, total_duration=10.0, padding=0.05)
    assert len(segments) == 3
    assert segments[0]["start"] == 0.0
    assert segments[0]["end"] > 1.9  # ~2.0 + padding
    assert segments[-1]["end"] == 10.0


def test_build_speech_segments_no_silence():
    segments = build_speech_segments([], total_duration=10.0)
    assert len(segments) == 1
    assert segments[0]["start"] == 0.0
    assert segments[0]["end"] == 10.0


def test_build_trim_filter_generates_concat():
    segments = [
        {"start": 0.0, "end": 2.0},
        {"start": 3.5, "end": 6.0},
    ]
    result = build_trim_filter(segments)
    assert "trim=" in result
    assert "atrim=" in result
    assert "concat=n=2" in result
    assert "[outv][outa]" in result


def test_build_trim_filter_empty():
    result = build_trim_filter([])
    assert result == ""


def test_build_speech_segments_adjacent_silences():
    """Adjacent silences should still produce valid segments."""
    silences = [
        {"start": 1.0, "end": 2.0},
        {"start": 2.1, "end": 3.0},
    ]
    segments = build_speech_segments(silences, total_duration=5.0, padding=0.05)
    # Should handle near-adjacent silences without producing tiny segments
    assert all(seg["end"] > seg["start"] for seg in segments)
