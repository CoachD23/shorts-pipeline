"""Auto-silence removal — detect and cut silent segments for tighter pacing."""
import subprocess
import re
from pathlib import Path


def detect_silences(
    input_path: str,
    noise_threshold: str = "-30dB",
    min_duration: float = 0.5,
) -> list[dict]:
    """Detect silent segments in a video using FFmpeg silencedetect.

    Args:
        input_path: Path to video file.
        noise_threshold: Audio level below which is considered silence (e.g. "-30dB").
        min_duration: Minimum silence duration in seconds to detect.

    Returns:
        List of dicts with 'start' and 'end' keys (seconds).
    """
    result = subprocess.run(
        [
            "ffmpeg", "-i", input_path,
            "-af", f"silencedetect=noise={noise_threshold}:d={min_duration}",
            "-f", "null", "-",
        ],
        capture_output=True, text=True,
    )

    stderr = result.stderr
    silences = []
    starts = re.findall(r"silence_start: ([\d.]+)", stderr)
    ends = re.findall(r"silence_end: ([\d.]+)", stderr)

    for start, end in zip(starts, ends):
        silences.append({"start": float(start), "end": float(end)})

    return silences


def build_speech_segments(
    silences: list[dict],
    total_duration: float,
    padding: float = 0.05,
) -> list[dict]:
    """Convert silence regions into speech (non-silent) segments.

    Args:
        silences: List of silence dicts with 'start' and 'end'.
        total_duration: Total video duration in seconds.
        padding: Extra seconds to keep at silence boundaries for natural cuts.

    Returns:
        List of dicts with 'start' and 'end' for speech segments.
    """
    if not silences:
        return [{"start": 0, "end": total_duration}]

    segments = []
    prev_end = 0.0

    for silence in silences:
        speech_start = prev_end
        speech_end = silence["start"] + padding
        if speech_end > speech_start + 0.1:  # Min segment length
            segments.append({"start": speech_start, "end": speech_end})
        prev_end = max(0, silence["end"] - padding)

    # Final segment after last silence
    if prev_end < total_duration:
        segments.append({"start": prev_end, "end": total_duration})

    return segments


def get_video_duration(input_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            input_path,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def build_trim_filter(segments: list[dict]) -> str:
    """Build FFmpeg filter_complex for concatenating speech segments.

    Returns a filter_complex string that trims and concatenates segments.
    """
    if not segments:
        return ""

    parts = []
    for i, seg in enumerate(segments):
        parts.append(
            f"[0:v]trim=start={seg['start']:.3f}:end={seg['end']:.3f},setpts=PTS-STARTPTS[v{i}];"
            f"[0:a]atrim=start={seg['start']:.3f}:end={seg['end']:.3f},asetpts=PTS-STARTPTS[a{i}];"
        )

    # Concat all segments
    v_labels = "".join(f"[v{i}]" for i in range(len(segments)))
    a_labels = "".join(f"[a{i}]" for i in range(len(segments)))
    parts.append(f"{v_labels}{a_labels}concat=n={len(segments)}:v=1:a=1[outv][outa]")

    return "".join(parts)


def remove_silence(
    input_path: str,
    output_path: str,
    noise_threshold: str = "-30dB",
    min_duration: float = 0.5,
) -> str:
    """Remove silent segments from a video.

    Args:
        input_path: Path to input video.
        output_path: Path for output video with silences removed.
        noise_threshold: Audio level threshold for silence detection.
        min_duration: Minimum silence duration to remove.

    Returns:
        Path to the output video.
    """
    silences = detect_silences(input_path, noise_threshold, min_duration)

    if not silences:
        # No silence found — copy as-is
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path],
            capture_output=True, check=True,
        )
        return output_path

    duration = get_video_duration(input_path)
    segments = build_speech_segments(silences, duration)
    filter_complex = build_trim_filter(segments)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "[outa]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            output_path,
        ],
        capture_output=True, check=True,
    )

    return output_path
