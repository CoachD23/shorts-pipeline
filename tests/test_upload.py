"""Tests for YouTube upload module."""
from src.upload import build_video_metadata


def test_build_video_metadata_has_required_fields():
    meta = build_video_metadata(
        title="Chin Dribble Weave Entry",
        description="Test description",
        tags=["Princeton Offense", "Basketball"],
        privacy="private",
    )
    assert meta["snippet"]["title"] == "Chin Dribble Weave Entry"
    assert meta["snippet"]["description"] == "Test description"
    assert meta["snippet"]["tags"] == ["Princeton Offense", "Basketball"]
    assert meta["status"]["privacyStatus"] == "private"
    assert meta["snippet"]["categoryId"] == "17"


def test_build_video_metadata_defaults_to_private():
    meta = build_video_metadata(
        title="Test", description="Test", tags=[], privacy=None,
    )
    assert meta["status"]["privacyStatus"] == "private"
