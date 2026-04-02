#!/usr/bin/env python3
"""Flask web UI for Shorts Pipeline."""
import json
import os
import threading
from datetime import date
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory

# Ensure our bundled ffmpeg/ffprobe (with libass) are on PATH first, then Homebrew
project_bin = str(Path(__file__).parent / "bin")
homebrew_bin = "/opt/homebrew/bin"
os.environ["PATH"] = project_bin + ":" + homebrew_bin + ":" + os.environ.get("PATH", "")

app = Flask(__name__, template_folder="web", static_folder="web/static")

# Pipeline status tracking
pipeline_status = {
    "running": False,
    "stage": "",
    "progress": 0,
    "error": "",
    "result": None,
}


def run_pipeline_async(video_path, title, hook, accent, crop, source_image, no_filter, no_music):
    """Run pipeline in background thread, updating status."""
    global pipeline_status
    try:
        pipeline_status["running"] = True
        pipeline_status["error"] = ""
        pipeline_status["result"] = None

        import yaml
        from src.transcribe import transcribe_video, save_transcript
        from src.captions import save_captions
        from src.thumbnail import generate_thumbnail
        from src.description import save_description, save_instagram_caption, save_blog_embed
        from src.video import process_video, extract_frame
        from src.hooks import detect_hook
        from src.music import find_music_file

        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        slug = title.lower().replace(" ", "-")[:40]
        output_dir = Path("output") / f"{date.today().isoformat()}-{slug}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Stage 1: Transcribe
        pipeline_status["stage"] = "Transcribing with Whisper..."
        pipeline_status["progress"] = 10
        transcript = transcribe_video(video_path, model_size="base")

        # Auto-detect hook if not provided
        if not hook:
            hook_result = detect_hook(transcript)
            if hook_result["score"] > 0.2:
                hook = hook_result["hook_text"]
                accent = hook_result["accent_word"]

        # Stage 2: Save transcript
        pipeline_status["stage"] = "Saving transcript..."
        pipeline_status["progress"] = 25
        json_path, md_path = save_transcript(transcript, output_dir, title)

        # Stage 3: Captions
        pipeline_status["stage"] = "Generating kinetic captions..."
        pipeline_status["progress"] = 40
        ass_path = save_captions(transcript, config, output_dir)

        # Stage 4: Thumbnail
        pipeline_status["stage"] = "Generating thumbnail..."
        pipeline_status["progress"] = 55
        if source_image and Path(source_image).exists():
            frame_path = source_image
        else:
            frame_path = extract_frame(video_path, str(output_dir / "frame.png"), timestamp=1.0)

        thumb_config = config
        if no_filter:
            thumb_config = {**config, "thumbnail": {**config.get("thumbnail", {}), "cartoon_strength": "none"}}

        thumb_path = generate_thumbnail(
            source_image_path=frame_path,
            hook_text=hook or title.upper(),
            accent_word=accent or title.split()[-1].upper(),
            config=thumb_config,
            output_dir=str(output_dir),
        )

        # Stage 5: Description + Instagram + Blog embed
        pipeline_status["stage"] = "Generating descriptions..."
        pipeline_status["progress"] = 70
        desc_path = save_description(transcript, title, config, output_dir)
        ig_path = save_instagram_caption(transcript, title, config, output_dir)
        blog_path = save_blog_embed(transcript, title, config, output_dir)

        # Stage 6: Video processing
        pipeline_status["stage"] = "Processing video with FFmpeg..."
        pipeline_status["progress"] = 85
        video_outputs = process_video(
            input_path=video_path,
            ass_path=str(ass_path),
            output_dir=str(output_dir),
            crop_strategy=crop,
        )

        pipeline_status["stage"] = "Complete!"
        pipeline_status["progress"] = 100
        pipeline_status["result"] = {
            "output_dir": str(output_dir),
            "thumbnail": os.path.basename(thumb_path),
            "description": desc_path.read_text() if desc_path.exists() else "",
            "instagram": ig_path.read_text() if ig_path.exists() else "",
            "blog_embed": blog_path.read_text() if blog_path.exists() else "",
            "transcript": md_path.read_text() if md_path.exists() else "",
            "videos": {k: os.path.basename(v) for k, v in video_outputs.items()},
        }

    except Exception as e:
        pipeline_status["error"] = str(e)
        pipeline_status["stage"] = "Error"
    finally:
        pipeline_status["running"] = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/reset", methods=["POST"])
def reset():
    """Clear error state so a new job can start."""
    global pipeline_status
    if not pipeline_status["running"]:
        pipeline_status = {"running": False, "stage": "", "progress": 0, "error": "", "result": None}
    return jsonify({"status": "reset"})


@app.route("/api/process", methods=["POST"])
def process():
    global pipeline_status
    if pipeline_status["running"]:
        return jsonify({"error": "Pipeline already running"}), 409

    # Clear any previous error state
    pipeline_status = {"running": False, "stage": "", "progress": 0, "error": "", "result": None}

    # Handle file upload or inbox file
    video_path = request.form.get("inbox_file", "")
    if video_path:
        video_path = str(Path("inbox") / video_path)
    else:
        video = request.files.get("video")
        if not video:
            return jsonify({"error": "No video file provided"}), 400

        # Validate file extension
        video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
        ext = Path(video.filename).suffix.lower()
        if ext not in video_exts:
            return jsonify({"error": f"Invalid file type '{ext}'. Upload a video file ({', '.join(video_exts)})"}), 400

        # Save uploaded file
        inbox = Path("inbox")
        inbox.mkdir(exist_ok=True)
        video_path = str(inbox / video.filename)
        video.save(video_path)

    title = request.form.get("title", "Untitled")
    hook = request.form.get("hook", "")
    accent = request.form.get("accent", "")
    crop = request.form.get("crop", "center")
    source_image = request.form.get("source_image", "")
    no_filter = request.form.get("no_filter") == "true"
    no_music = request.form.get("no_music") == "true"

    thread = threading.Thread(
        target=run_pipeline_async,
        args=(video_path, title, hook, accent, crop, source_image, no_filter, no_music),
    )
    thread.start()

    return jsonify({"status": "started"})


@app.route("/api/status")
def status():
    return jsonify(pipeline_status)


@app.route("/api/inbox")
def list_inbox():
    inbox = Path("inbox")
    if not inbox.exists():
        return jsonify({"files": []})
    exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    files = [f.name for f in inbox.iterdir() if f.suffix.lower() in exts]
    return jsonify({"files": sorted(files)})


@app.route("/api/outputs")
def list_outputs():
    output_dir = Path("output")
    if not output_dir.exists():
        return jsonify({"folders": []})
    folders = sorted([d.name for d in output_dir.iterdir() if d.is_dir()], reverse=True)
    return jsonify({"folders": folders})


@app.route("/output/<path:filepath>")
def serve_output(filepath):
    return send_from_directory("output", filepath)


if __name__ == "__main__":
    print("\n🏀 Shorts Pipeline UI")
    print("   Open: http://localhost:8080\n")
    app.run(debug=False, port=8080, host="0.0.0.0")
