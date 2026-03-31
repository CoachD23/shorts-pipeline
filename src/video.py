"""Video processing — FFmpeg commands for cropping and caption burn-in."""
import subprocess
from pathlib import Path


def detect_orientation(width: int, height: int) -> str:
    """Detect video orientation from dimensions."""
    ratio = width / height
    if ratio > 1.2:
        return "horizontal"
    elif ratio < 0.8:
        return "vertical"
    return "square"


def _get_video_dimensions(input_path: str) -> tuple[int, int]:
    """Probe video dimensions using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=x",
            input_path,
        ],
        capture_output=True, text=True, check=True,
    )
    w, h = result.stdout.strip().split("x")
    return int(w), int(h)


def build_ffmpeg_commands(
    input_path: str,
    ass_path: str,
    output_dir: str,
    input_width: int,
    input_height: int,
    crop_strategy: str = "center",
) -> list[list[str]]:
    """Build FFmpeg command lists for all three output variants.

    Returns list of 3 command lists: [short-captioned, embed-captioned, no-captions]
    """
    orientation = detect_orientation(input_width, input_height)
    commands = []

    # 1. Short (vertical 1080x1920, captioned)
    if orientation == "vertical":
        vf_short = f"ass={ass_path}"
    elif crop_strategy == "blur":
        vf_short = (
            f"split[original][blur];"
            f"[blur]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,boxblur=20:20[bg];"
            f"[original]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,"
            f"ass={ass_path}"
        )
    else:
        crop_h = input_height
        crop_w = int(crop_h * 9 / 16)
        if crop_w > input_width:
            crop_w = input_width
            crop_h = int(crop_w * 16 / 9)
        vf_short = (
            f"crop={crop_w}:{crop_h}:(iw-{crop_w})/2:(ih-{crop_h})/2,"
            f"scale=1080:1920,"
            f"ass={ass_path}"
        )

    commands.append([
        "ffmpeg", "-y", "-i", input_path,
        "-vf", vf_short,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(Path(output_dir) / "short-captioned.mp4"),
    ])

    # 2. Embed (original aspect ratio, captioned)
    commands.append([
        "ffmpeg", "-y", "-i", input_path,
        "-vf", f"ass={ass_path}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(Path(output_dir) / "embed-captioned.mp4"),
    ])

    # 3. No captions (clean, for CapCut)
    commands.append([
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(Path(output_dir) / "no-captions.mp4"),
    ])

    return commands


def extract_frame(input_path: str, output_path: str, timestamp: float = 1.0) -> str:
    """Extract a single frame from video for thumbnail source."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-ss", str(timestamp),
            "-i", input_path,
            "-frames:v", "1", "-q:v", "2",
            output_path,
        ],
        capture_output=True, check=True,
    )
    return output_path


def process_video(
    input_path: str,
    ass_path: str,
    output_dir: str,
    crop_strategy: str = "center",
) -> dict[str, str]:
    """Run all FFmpeg commands to produce output videos."""
    width, height = _get_video_dimensions(input_path)
    commands = build_ffmpeg_commands(
        input_path, ass_path, output_dir, width, height, crop_strategy
    )
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    outputs = {}
    names = ["short-captioned.mp4", "embed-captioned.mp4", "no-captions.mp4"]
    for cmd, name in zip(commands, names):
        subprocess.run(cmd, capture_output=True, check=True)
        outputs[name] = str(output_dir_path / name)
    return outputs
