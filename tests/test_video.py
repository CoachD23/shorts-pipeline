"""Tests for video processing (crop + caption burn-in)."""
from src.video import build_ffmpeg_commands, detect_orientation


def test_detect_orientation_horizontal():
    assert detect_orientation(1920, 1080) == "horizontal"


def test_detect_orientation_vertical():
    assert detect_orientation(1080, 1920) == "vertical"


def test_detect_orientation_square():
    assert detect_orientation(1080, 1080) == "square"


def test_build_ffmpeg_commands_vertical_input():
    cmds = build_ffmpeg_commands(
        input_path="input.mp4", ass_path="captions.ass",
        output_dir="/out", input_width=1080, input_height=1920, crop_strategy="center",
    )
    assert len(cmds) == 3
    assert any("short-captioned.mp4" in cmd[-1] for cmd in cmds)
    assert any("embed-captioned.mp4" in cmd[-1] for cmd in cmds)
    assert any("no-captions.mp4" in cmd[-1] for cmd in cmds)


def test_build_ffmpeg_commands_horizontal_center_crop():
    cmds = build_ffmpeg_commands(
        input_path="input.mp4", ass_path="captions.ass",
        output_dir="/out", input_width=1920, input_height=1080, crop_strategy="center",
    )
    short_cmd = [c for c in cmds if "short-captioned.mp4" in c[-1]][0]
    cmd_str = " ".join(short_cmd)
    assert "crop=" in cmd_str
