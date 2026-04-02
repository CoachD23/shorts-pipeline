"""Tests for clip extraction."""
from src.clips import score_segment, find_clip_boundaries


def test_score_segment_with_hooks():
    seg = {"start": 0, "end": 30, "text": "Here's the secret to breaking every zone defense"}
    score = score_segment(seg)
    assert score > 0.3


def test_score_segment_boring():
    seg = {"start": 0, "end": 30, "text": "the ball goes here and then there"}
    score = score_segment(seg)
    assert score < 0.5


def test_score_segment_ideal_length():
    seg = {"start": 0, "end": 30, "text": "This is the key play that destroys zones"}
    score = score_segment(seg)
    assert score > 0.4


def test_find_clip_boundaries_returns_clips():
    transcript = {
        "segments": [
            {"start": 0, "end": 20, "text": "Here is the secret to beating any zone defense."},
            {"start": 20, "end": 40, "text": "The point guard reads the defense and makes the cut."},
            {"start": 40, "end": 60, "text": "This play always works against a 2-3 zone."},
            {"start": 70, "end": 90, "text": "Now let me show you a different approach."},
            {"start": 90, "end": 110, "text": "Watch how the backdoor cut destroys the press."},
        ]
    }
    clips = find_clip_boundaries(transcript, min_duration=15, max_clips=3)
    assert len(clips) > 0
    assert all("start" in c and "end" in c and "score" in c for c in clips)


def test_find_clip_boundaries_empty():
    clips = find_clip_boundaries({"segments": []})
    assert clips == []


def test_find_clip_boundaries_no_overlap():
    transcript = {
        "segments": [
            {"start": 0, "end": 30, "text": "First play destroys zones."},
            {"start": 30, "end": 60, "text": "Second play beats man defense."},
        ]
    }
    clips = find_clip_boundaries(transcript, min_duration=10, max_clips=5)
    # No two clips should overlap
    for i in range(len(clips)):
        for j in range(i + 1, len(clips)):
            assert clips[i]["end"] <= clips[j]["start"] or clips[j]["end"] <= clips[i]["start"]
