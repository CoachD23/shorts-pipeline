"""Tests for YouTube description generator."""
from src.description import generate_description, detect_timestamps, generate_instagram_caption, generate_blog_embed, generate_pinned_comment


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


def test_generate_blog_embed_with_video_id():
    transcript = {"text": "This is a test transcript.", "segments": []}
    config = {"blog": {"base_url": "https://test.com/blog"}}
    html = generate_blog_embed(transcript, "Test Video", config, video_id="abc123")
    assert "abc123" in html
    assert "<iframe" in html
    assert "Test Video" in html
    assert "This is a test transcript" in html

def test_generate_blog_embed_no_video_id():
    transcript = {"text": "Test.", "segments": []}
    config = {"blog": {"base_url": "https://test.com/blog"}}
    html = generate_blog_embed(transcript, "Test", config, video_id="")
    assert "VIDEO_ID" in html

def test_generate_pinned_comment():
    transcript = {"text": "This play breaks every zone defense.", "segments": []}
    result = generate_pinned_comment(transcript, "Test")
    assert "PINNED COMMENT OPTIONS" in result
    assert "1." in result
    assert "2." in result
    assert "3." in result
