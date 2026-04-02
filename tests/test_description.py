"""Tests for YouTube description generator."""
from src.description import generate_description, detect_timestamps, generate_instagram_caption


def test_detect_timestamps_finds_pauses():
    segments = [
        {"start": 0.0, "end": 3.0, "text": "This is the setup."},
        {"start": 3.0, "end": 6.0, "text": "The point guard dribbles right."},
        {"start": 8.0, "end": 11.0, "text": "Now the backdoor cut happens."},
        {"start": 11.0, "end": 14.0, "text": "And that is how you score."},
    ]
    timestamps = detect_timestamps(segments, pause_threshold=1.5)
    assert len(timestamps) >= 2


def test_generate_description_contains_required_sections():
    transcript = {
        "text": "This play breaks every zone defense. The point guard starts with a dribble weave.",
        "segments": [
            {"start": 0.0, "end": 3.0, "text": "This play breaks every zone defense."},
            {"start": 3.0, "end": 6.0, "text": "The point guard starts with a dribble weave."},
        ]
    }
    config = {
        "youtube": {"default_tags": ["Princeton Offense", "Basketball Coaching"]},
        "blog": {"base_url": "https://coachprincetonbasketball.com/blog"},
    }
    desc = generate_description(transcript=transcript, title="Chin Dribble Weave Entry", config=config)
    assert "Chin Dribble Weave Entry" in desc
    assert "coachprincetonbasketball.com/blog" in desc
    assert "#PrincetonOffense" in desc
    assert "0:00" in desc


def test_generate_instagram_caption():
    transcript = {
        "text": "This play breaks every zone. The point guard starts the weave.",
        "segments": []
    }
    config = {"youtube": {"default_tags": ["Princeton Offense"]}}
    caption = generate_instagram_caption(transcript, "Chin Entry", config)
    assert "This play breaks every zone" in caption
    assert "#PrincetonOffense" in caption
    assert "#BasketballTips" in caption
    assert "link in bio" in caption
