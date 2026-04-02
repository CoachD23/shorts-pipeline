"""Tests for pipeline checkpoint system."""
from pathlib import Path
from src.checkpoint import (
    load_checkpoint, save_checkpoint, is_stage_complete,
    get_stage_artifacts, clear_checkpoint,
)


def test_load_checkpoint_empty(tmp_path):
    state = load_checkpoint(tmp_path)
    assert "stages" in state
    assert state["stages"] == {}


def test_save_and_load_checkpoint(tmp_path):
    save_checkpoint(tmp_path, "transcribe", {"json": str(tmp_path / "t.json")})
    state = load_checkpoint(tmp_path)
    assert "transcribe" in state["stages"]
    assert state["stages"]["transcribe"]["status"] == "complete"


def test_is_stage_complete_true(tmp_path):
    artifact = tmp_path / "output.txt"
    artifact.write_text("data")
    save_checkpoint(tmp_path, "transcribe", {"file": str(artifact)})
    assert is_stage_complete(tmp_path, "transcribe") is True


def test_is_stage_complete_false_no_stage(tmp_path):
    assert is_stage_complete(tmp_path, "transcribe") is False


def test_is_stage_complete_false_missing_artifact(tmp_path):
    save_checkpoint(tmp_path, "transcribe", {"file": str(tmp_path / "missing.txt")})
    assert is_stage_complete(tmp_path, "transcribe") is False


def test_get_stage_artifacts(tmp_path):
    save_checkpoint(tmp_path, "captions", {"ass": "/path/to/captions.ass"})
    arts = get_stage_artifacts(tmp_path, "captions")
    assert arts["ass"] == "/path/to/captions.ass"


def test_clear_checkpoint(tmp_path):
    save_checkpoint(tmp_path, "test", {"x": "y"})
    assert (tmp_path / "pipeline_state.json").exists()
    clear_checkpoint(tmp_path)
    assert not (tmp_path / "pipeline_state.json").exists()
