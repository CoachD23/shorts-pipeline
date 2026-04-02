"""Background music with automatic voice ducking based on speech timestamps."""
import random
from pathlib import Path


def find_music_file(music_dir: str = "music") -> str | None:
    """Find a random music file from the music directory."""
    music_path = Path(music_dir)
    if not music_path.exists():
        return None
    music_files = list(music_path.glob("*.mp3")) + list(music_path.glob("*.wav"))
    if not music_files:
        return None
    return str(random.choice(music_files))


def build_volume_filter(
    transcript: dict,
    speech_volume: float = 0.10,
    gap_volume: float = 0.25,
    buffer: float = 0.3,
) -> str:
    """Build FFmpeg volume filter that ducks music during speech.

    Uses Whisper word timestamps to detect speech regions.
    Music plays at gap_volume normally, ducks to speech_volume when someone is talking.

    Args:
        transcript: Whisper transcript with segments containing start/end times.
        speech_volume: Music volume during speech (0.0-1.0).
        gap_volume: Music volume during silence/gaps (0.0-1.0).
        buffer: Extra seconds of ducking before/after speech.

    Returns:
        FFmpeg volume filter string like:
        volume='if(between(t,0.0,2.5),0.10,if(between(t,3.0,5.5),0.10,0.25))'
    """
    segments = transcript.get("segments", [])
    if not segments:
        return f"volume={gap_volume:.2f}"

    # Merge overlapping/adjacent speech regions with buffer
    speech_regions = []
    for seg in segments:
        start = max(0, seg["start"] - buffer)
        end = seg["end"] + buffer
        if speech_regions and start <= speech_regions[-1][1]:
            speech_regions[-1] = (speech_regions[-1][0], max(end, speech_regions[-1][1]))
        else:
            speech_regions.append((start, end))

    if not speech_regions:
        return f"volume={gap_volume:.2f}"

    # Build nested if(between()) expression
    # Start from innermost (default = gap_volume) and wrap outward
    expr = f"{gap_volume:.2f}"
    for start, end in reversed(speech_regions):
        expr = f"if(between(t\\,{start:.2f}\\,{end:.2f})\\,{speech_volume:.2f}\\,{expr})"

    return f"volume='{expr}'"


def build_music_ffmpeg_args(
    music_path: str,
    transcript: dict,
    speech_volume: float = 0.10,
    gap_volume: float = 0.25,
) -> list[str]:
    """Build FFmpeg arguments to mix background music with voice ducking.

    Returns additional FFmpeg args to insert before the output file path.
    These args add the music as a second input, apply volume ducking,
    and mix it with the original audio.

    Args:
        music_path: Path to music file.
        transcript: Whisper transcript for speech detection.
        speech_volume: Music volume during speech.
        gap_volume: Music volume during gaps.

    Returns:
        List of FFmpeg argument strings to add to the command.
    """
    vol_filter = build_volume_filter(transcript, speech_volume, gap_volume)

    return [
        "-i", music_path,
        "-filter_complex",
        f"[1:a]{vol_filter},aloop=loop=-1:size=2e+09[music];"
        f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v",
        "-map", "[aout]",
    ]
