"""Pipeline checkpoint system — save/resume progress to avoid re-processing."""
import json
from pathlib import Path
from datetime import datetime


CHECKPOINT_FILE = "pipeline_state.json"


def load_checkpoint(output_dir: Path) -> dict:
    """Load checkpoint state from output directory.

    Returns dict with completed stages and their artifact paths.
    """
    checkpoint_path = output_dir / CHECKPOINT_FILE
    if checkpoint_path.exists():
        return json.loads(checkpoint_path.read_text())
    return {"stages": {}, "started_at": datetime.now().isoformat()}


def save_checkpoint(output_dir: Path, stage: str, artifacts: dict) -> None:
    """Mark a stage as complete with its output artifacts.

    Args:
        output_dir: Pipeline output directory.
        stage: Stage name (e.g. 'transcribe', 'captions', 'thumbnail').
        artifacts: Dict of artifact name -> file path produced by this stage.
    """
    state = load_checkpoint(output_dir)
    state["stages"][stage] = {
        "status": "complete",
        "completed_at": datetime.now().isoformat(),
        "artifacts": artifacts,
    }
    checkpoint_path = output_dir / CHECKPOINT_FILE
    checkpoint_path.write_text(json.dumps(state, indent=2))


def is_stage_complete(output_dir: Path, stage: str) -> bool:
    """Check if a stage has already been completed."""
    state = load_checkpoint(output_dir)
    stage_info = state.get("stages", {}).get(stage, {})
    if stage_info.get("status") != "complete":
        return False
    # Verify artifacts still exist
    for path in stage_info.get("artifacts", {}).values():
        if not Path(path).exists():
            return False
    return True


def get_stage_artifacts(output_dir: Path, stage: str) -> dict:
    """Get artifact paths from a completed stage."""
    state = load_checkpoint(output_dir)
    return state.get("stages", {}).get(stage, {}).get("artifacts", {})


def clear_checkpoint(output_dir: Path) -> None:
    """Remove checkpoint file to force full re-processing."""
    checkpoint_path = output_dir / CHECKPOINT_FILE
    if checkpoint_path.exists():
        checkpoint_path.unlink()
