"""Seamless loop detection — analyze if a Short loops visually."""
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image


def extract_first_last_frames(
    video_path: str,
    output_dir: str,
) -> tuple[str, str]:
    """Extract the first and last frame from a video.

    Returns tuple of (first_frame_path, last_frame_path).
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    first_path = str(Path(output_dir) / "loop_first.png")
    last_path = str(Path(output_dir) / "loop_last.png")

    # First frame
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-frames:v", "1", "-q:v", "2", first_path],
        capture_output=True, check=True,
    )

    # Last frame — seek to near end
    # Get duration first
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video_path],
        capture_output=True, text=True, check=True,
    )
    duration = float(result.stdout.strip())
    last_time = max(0, duration - 0.1)

    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(last_time), "-i", video_path, "-frames:v", "1", "-q:v", "2", last_path],
        capture_output=True, check=True,
    )

    return first_path, last_path


def calculate_frame_similarity(frame1_path: str, frame2_path: str) -> float:
    """Calculate visual similarity between two frames (0.0 = different, 1.0 = identical).

    Uses normalized pixel difference — simple and fast.
    """
    img1 = Image.open(frame1_path).convert("RGB").resize((320, 180))
    img2 = Image.open(frame2_path).convert("RGB").resize((320, 180))

    arr1 = np.array(img1, dtype=np.float32)
    arr2 = np.array(img2, dtype=np.float32)

    # Mean absolute difference, normalized to 0-1
    diff = np.abs(arr1 - arr2).mean() / 255.0
    similarity = 1.0 - diff

    return round(similarity, 3)


def detect_loop(video_path: str, output_dir: str) -> dict:
    """Analyze if a video loops seamlessly.

    Returns:
        Dict with:
        - similarity: 0.0-1.0 score
        - is_loopable: True if similarity > 0.85
        - recommendation: Human-readable advice
    """
    try:
        first_path, last_path = extract_first_last_frames(video_path, output_dir)
        similarity = calculate_frame_similarity(first_path, last_path)
    except Exception:
        return {
            "similarity": 0.0,
            "is_loopable": False,
            "recommendation": "Could not analyze loop — video may be too short.",
        }

    if similarity >= 0.92:
        recommendation = "Excellent loop! First and last frames are nearly identical. This will drive rewatches."
    elif similarity >= 0.85:
        recommendation = "Good loop potential. Minor differences between start/end. Consider trimming for a tighter loop."
    elif similarity >= 0.70:
        recommendation = "Moderate loop. Viewers may notice the cut. Try filming your ending to match your opening."
    else:
        recommendation = "Not loopable. Start and end look very different. For better rewatches, film the ending to visually match the opening."

    return {
        "similarity": similarity,
        "is_loopable": similarity >= 0.85,
        "recommendation": recommendation,
    }
