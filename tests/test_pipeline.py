"""Tests for main pipeline orchestrator."""
from unittest.mock import patch, MagicMock
from pathlib import Path
from PIL import Image
from src.pipeline import run_pipeline


@patch("src.pipeline.upload_video")
@patch("src.pipeline.process_video")
@patch("src.pipeline.generate_thumbnail")
@patch("src.pipeline.save_description")
@patch("src.pipeline.save_captions")
@patch("src.pipeline.save_transcript")
@patch("src.pipeline.transcribe_video")
@patch("src.pipeline.extract_frame")
@patch("src.pipeline.load_config")
def test_run_pipeline_creates_output_dir(
    mock_config, mock_frame, mock_transcribe, mock_save_transcript,
    mock_save_captions, mock_save_desc, mock_thumb, mock_process, mock_upload,
    tmp_path,
):
    """Pipeline should call all modules in order and return output paths."""
    mock_config.return_value = {
        "brand": {"primary_color": "#FFFFFF", "accent_color": "#FFFF00",
                  "font": "Montserrat-ExtraBold", "stroke_color": "#000000", "stroke_width": 4},
        "captions": {"words_per_group": 3, "font_size": 65, "position": "center_above_middle"},
        "thumbnail": {"width": 1280, "height": 720, "cartoon_strength": "medium", "text_position": "right"},
        "youtube": {"channel_id": "test", "default_tags": ["test"], "default_privacy": "private"},
        "blog": {"base_url": "https://test.com/blog"},
    }
    mock_transcribe.return_value = {
        "text": "Test.", "segments": [{"start": 0, "end": 1, "text": "Test.",
                                       "words": [{"word": "Test", "start": 0, "end": 1}]}]
    }
    mock_save_transcript.return_value = (tmp_path / "t.json", tmp_path / "t.md")
    mock_save_captions.return_value = tmp_path / "captions.ass"
    mock_frame.return_value = str(tmp_path / "frame.png")
    mock_thumb.return_value = str(tmp_path / "thumb.jpg")
    mock_save_desc.return_value = tmp_path / "desc.txt"
    mock_process.return_value = {"short-captioned.mp4": "out.mp4"}

    Image.new("RGB", (100, 100)).save(tmp_path / "frame.png")

    result = run_pipeline(
        input_path=str(tmp_path / "fake.mp4"),
        title="Test Video",
        hook_text="TEST HOOK",
        accent_word="HOOK",
        crop_strategy="center",
        upload=False,
        config_path=str(tmp_path / "config.yaml"),
        output_base=str(tmp_path / "output"),
    )

    assert "output_dir" in result
    assert "thumbnail" in result
    assert "videos" in result
    assert mock_transcribe.called
    assert mock_save_captions.called
    assert mock_thumb.called
    assert mock_process.called
    assert not mock_upload.called  # upload=False
