"""Tests for background music with voice ducking."""
from src.music import build_volume_filter, find_music_file, build_music_ffmpeg_args


def test_build_volume_filter_with_speech():
    transcript = {
        "segments": [
            {"start": 0.5, "end": 2.0},
            {"start": 3.0, "end": 5.0},
        ]
    }
    result = build_volume_filter(transcript, speech_volume=0.10, gap_volume=0.25, buffer=0.3)
    assert "volume=" in result
    assert "between" in result
    assert "0.10" in result
    assert "0.25" in result


def test_build_volume_filter_empty_transcript():
    transcript = {"segments": []}
    result = build_volume_filter(transcript)
    assert result == "volume=0.25"


def test_build_volume_filter_no_segments():
    transcript = {}
    result = build_volume_filter(transcript)
    assert result == "volume=0.25"


def test_find_music_file_no_dir(tmp_path):
    result = find_music_file(str(tmp_path / "nonexistent"))
    assert result is None


def test_find_music_file_empty_dir(tmp_path):
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    result = find_music_file(str(music_dir))
    assert result is None


def test_find_music_file_with_files(tmp_path):
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    (music_dir / "track1.mp3").write_text("fake")
    result = find_music_file(str(music_dir))
    assert result is not None
    assert "track1.mp3" in result


def test_build_music_ffmpeg_args():
    transcript = {
        "segments": [{"start": 0.0, "end": 3.0}]
    }
    args = build_music_ffmpeg_args("music/track.mp3", transcript)
    assert "-i" in args
    assert "music/track.mp3" in args
    assert "-filter_complex" in args
    assert "amix" in args[args.index("-filter_complex") + 1]
