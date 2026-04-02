"""Clip extraction — find the best Short-worthy segments from a long video."""
import re
import subprocess
from pathlib import Path


def score_segment(segment: dict) -> float:
    """Score a transcript segment for clip-worthiness.

    Higher scores = more likely to be an engaging standalone clip.
    Looks for hook-worthy language, questions, emphasis words.
    """
    text = segment.get("text", "").lower().strip()
    score = 0.0

    if not text:
        return 0.0

    # Hook patterns
    hook_patterns = [
        r"\b(?:here's|here is|this is|watch|look at)\b",
        r"\b(?:key|secret|trick|mistake|important|critical)\b",
        r"\b(?:always|never|every|best|worst)\b",
        r"\b(?:destroys?|breaks?|beats?|stops?)\b",
        r"\?\s*$",
    ]
    for pattern in hook_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 0.2

    # Ideal segment length (15-45 seconds)
    duration = segment.get("end", 0) - segment.get("start", 0)
    if 15 <= duration <= 45:
        score += 0.3
    elif 10 <= duration <= 60:
        score += 0.15

    # Word density (not too sparse, not too packed)
    words = len(text.split())
    words_per_sec = words / max(duration, 0.1)
    if 2.0 <= words_per_sec <= 3.5:
        score += 0.2

    return min(score, 1.0)


def find_clip_boundaries(
    transcript: dict,
    min_duration: float = 15.0,
    max_duration: float = 59.0,
    max_clips: int = 5,
) -> list[dict]:
    """Find the best clip boundaries from a transcript.

    Groups consecutive segments into clip-length chunks,
    scores each, and returns the top candidates.

    Args:
        transcript: Whisper transcript with segments.
        min_duration: Minimum clip duration in seconds.
        max_duration: Maximum clip duration (59s for Shorts).
        max_clips: Maximum number of clips to return.

    Returns:
        List of dicts with 'start', 'end', 'text', 'score' sorted by score.
    """
    segments = transcript.get("segments", [])
    if not segments:
        return []

    candidates = []

    # Sliding window over segments
    for i in range(len(segments)):
        clip_text = []
        clip_start = segments[i]["start"]

        for j in range(i, len(segments)):
            clip_end = segments[j]["end"]
            duration = clip_end - clip_start
            clip_text.append(segments[j].get("text", "").strip())

            if duration > max_duration:
                break

            if duration >= min_duration:
                combined_segment = {
                    "start": clip_start,
                    "end": clip_end,
                    "text": " ".join(clip_text),
                }
                combined_segment["score"] = score_segment(combined_segment)
                candidates.append(combined_segment)

    # Sort by score, deduplicate overlapping clips
    candidates.sort(key=lambda x: x["score"], reverse=True)

    selected = []
    for candidate in candidates:
        # Check for overlap with already selected clips
        overlaps = False
        for sel in selected:
            if candidate["start"] < sel["end"] and candidate["end"] > sel["start"]:
                overlaps = True
                break
        if not overlaps:
            selected.append(candidate)
        if len(selected) >= max_clips:
            break

    return selected


def extract_clip(
    input_path: str,
    output_path: str,
    start: float,
    end: float,
) -> str:
    """Extract a clip from a video using FFmpeg.

    Args:
        input_path: Source video path.
        output_path: Output clip path.
        start: Start time in seconds.
        end: End time in seconds.

    Returns:
        Path to extracted clip.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", input_path,
            "-t", str(end - start),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            output_path,
        ],
        capture_output=True, check=True,
    )

    return output_path


def extract_clips_from_video(
    input_path: str,
    transcript: dict,
    output_dir: str,
    max_clips: int = 5,
) -> list[dict]:
    """Find and extract the best clips from a long video.

    Args:
        input_path: Path to long-form video.
        transcript: Whisper transcript.
        output_dir: Directory to save clips.
        max_clips: Max number of clips to extract.

    Returns:
        List of dicts with 'path', 'start', 'end', 'text', 'score'.
    """
    boundaries = find_clip_boundaries(transcript, max_clips=max_clips)

    results = []
    for i, clip in enumerate(boundaries, 1):
        clip_path = str(Path(output_dir) / f"clip_{i}.mp4")
        extract_clip(input_path, clip_path, clip["start"], clip["end"])
        results.append({
            "path": clip_path,
            "start": clip["start"],
            "end": clip["end"],
            "text": clip["text"][:100],
            "score": clip["score"],
        })

    return results
