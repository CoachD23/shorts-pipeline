"""Tests for cross-platform exports."""
from src.platforms import PLATFORMS


def test_platforms_have_required_specs():
    for name, spec in PLATFORMS.items():
        assert "width" in spec
        assert "height" in spec
        assert "max_seconds" in spec
        assert "bitrate" in spec
        assert "label" in spec


def test_youtube_short_spec():
    assert PLATFORMS["youtube_short"]["width"] == 1080
    assert PLATFORMS["youtube_short"]["height"] == 1920
    assert PLATFORMS["youtube_short"]["max_seconds"] == 60


def test_instagram_feed_is_square():
    assert PLATFORMS["instagram_feed"]["width"] == PLATFORMS["instagram_feed"]["height"]


def test_tiktok_matches_youtube():
    assert PLATFORMS["tiktok"]["width"] == PLATFORMS["youtube_short"]["width"]
    assert PLATFORMS["tiktok"]["height"] == PLATFORMS["youtube_short"]["height"]
