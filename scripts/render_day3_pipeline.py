import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import edge_tts
from playwright.async_api import async_playwright
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = BASE_DIR / "AI_SERIES" / "VIDEOS"

DAY_3_CONTENT = {
    "day": 3,
    "topic": "How Computers Actually 'Learn' (The Function Approximation Analogy)",
    "level": "Level 1: AI Fundamentals",
    "scenes": [
        {
            "id": "act1_function",
            "title": "Machine Learning as Function Approximation",
            "voice_script": "At its mathematical core, machine learning does not create consciousness. It solves for an unknown mathematical equation y equals f of x.",
            "html": """
            <div class="card">
                <div class="card-header">
                    <span class="pill pill-blue">The Core Equation</span>
                    <span class="card-title">y = f(x) Approximation</span>
                </div>
                <div style="font-size: 32px; line-height: 1.5; color: #CBD5E1; margin-bottom: 24px;">
                    In classical math, humans write the function <b>f(x)</b>.<br>
                    In machine learning, algorithms search for the function that best maps input features <b>x</b> to true targets <b>y</b>.
                </div>
                <div class="takeaway">
                    💡 <b>Universal Approximation:</b> Neural networks can approximate ANY continuous function given sufficient parameters.
                </div>
            </div>
            """
        },
        {
            "id": "act2_knobs",
            "title": "The Infinite Knob Board",
            "voice_script": "Imagine a soundboard with millions of sliders called weights. At first, all sliders are random and the output sounds like pure static noise.",
            "html": """
            <div class="card">
                <div class="card-header">
                    <span class="pill pill-purple">The Analogy</span>
                    <span class="card-title">Adjusting the Sliders</span>
                </div>
                <div style="font-size: 30px; line-height: 1.5; color: #CBD5E1; margin-bottom: 24px;">
                    Every slider is a continuous numerical <b>weight</b>.<br>
                    When the model makes an error, the loss function measures how far off the sound is from perfection.
                </div>
                <div class="takeaway" style="border-color: rgba(56, 189, 248, 0.4);">
                    📌 <b>Learning Loop:</b> Guess ➔ Measure Error ➔ Nudge Knobs in Direction of Reduced Error.
                </div>
            </div>
            """
        },
        {
            "id": "act3_loss_gradient",
            "title": "Loss & Gradients: Guiding the Search",
            "voice_script": "How does the machine know which sliders to turn? Calculus. The gradient reveals the exact slope of the error hill, directing every knob down the steepest path.",
            "html": """
            <div class="card">
                <div class="card-header">
                    <span class="pill pill-orange">The Engine</span>
                    <span class="card-title">Gradient-Directed Search</span>
                </div>
                <div style="font-size: 30px; line-height: 1.5; color: #CBD5E1; margin-bottom: 24px;">
                    Gradient descent is walking down a mountain in pitch fog.<br>
                    You cannot see the bottom, but your feet feel the slope under you.
                </div>
                <div class="code-box">
Loss = (Prediction - Target)²
Weight_new = Weight_old - (Learning_Rate × Gradient)
                </div>
                <div class="takeaway" style="border-color: rgba(251, 146, 60, 0.4);">
                    🔥 <b>The Secret:</b> Learning is not thinking. It is numerical optimization.
                </div>
            </div>
            """
        },
        {
            "id": "act4_recap",
            "title": "Day 03 Cheatsheet & Summary",
            "voice_script": "When a computer learns, it is simply minimizing mistakes across high-dimensional geometry. Tomorrow in Day four, we explore what actually constitutes a dataset. Follow NeuBench for the 90-day AI breakdown.",
            "html": """
            <div class="card">
                <div class="card-header">
                    <span class="pill pill-green">Day 03 Cheatsheet</span>
                    <span class="card-title">Summary Checklist</span>
                </div>
                <div style="font-size: 28px; line-height: 1.6; color: #F1F5F9; display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px;">
                    <div>1️⃣ <b>Models are Functions:</b> Approximating complex input-output relationships.</div>
                    <div>2️⃣ <b>Weights are Knobs:</b> Numerical parameters tuned during training.</div>
                    <div>3️⃣ <b>Gradients are Compasses:</b> Pointing toward the lowest possible error.</div>
                </div>
                <div class="takeaway" style="background: rgba(34, 211, 238, 0.1); border-color: #22D3EE; text-align: center;">
                    ⚡ <b>Tomorrow (Day 04):</b> What is a Dataset? Inputs, Targets & Data Quality.
                </div>
            </div>
            """
        }
    ]
}

def generate_subtitles_srt(scenes: List[Dict[str, Any]], durations: List[float], srt_path: Path):
    srt_lines = []
    current_time = 0.0

    def format_srt_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    for i, (sc, dur) in enumerate(zip(scenes, durations)):
        start_t = current_time
        end_t = current_time + dur
        srt_lines.append(f"{i+1}")
        srt_lines.append(f"{format_srt_time(start_t)} --> {format_srt_time(end_t)}")
        srt_lines.append(sc["voice_script"])
        srt_lines.append("")
        current_time = end_t

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
    print(f"[Subtitles] SRT saved: {srt_path}")

async def render_day3_pipeline():
    day_dir = VIDEOS_DIR / "DAY_003"
    frames_dir = day_dir / "ANIM_FRAMES"
    day_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    scenes = DAY_3_CONTENT["scenes"]
    template_path = BASE_DIR / "src" / "templates" / "animated_short_template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    print("[Day3 Pipeline] 1. Generating Andrew Neural voiceovers...")
    durations = [14.0, 14.0, 14.0, 14.0]
    full_script = " ".join([sc["voice_script"] for sc in scenes])
    master_audio_path = day_dir / "enriched_andrew.mp3"
    tts = edge_tts.Communicate(full_script, "en-US-AndrewMultilingualNeural", rate="+3%")
    await tts.save(str(master_audio_path))
    print(f"[Day3 Pipeline] Audio saved to {master_audio_path}")

    print("[Day3 Pipeline] 2. Rendering high-res frames with Safe-Zone padding...")
    frame_paths = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})

        for i, sc in enumerate(scenes):
            frame_img = str(frames_dir / f"scene_{i+1:02d}.png")
            print(f"  -> Rendering Scene {i+1}: {sc['title']}...")

            rendered_html = html_template.replace(
                '<div class="series-tag">AI Explained • Day 01</div>',
                '<div class="series-tag">AI Explained • Day 03</div>'
            ).replace(
                '<div class="hero-concept" id="scene-title">Rules-Based Code vs. Learned Behavior</div>',
                f'<div class="hero-concept" id="scene-title">{sc["title"]}</div>'
            ).replace(
                '<div class="stage" id="stage-content">\n    <!-- Populated per scene -->\n  </div>',
                f'<div class="stage" id="stage-content">\n{sc["html"]}\n</div>'
            ).replace(
                '<!-- Dynamic caption text -->',
                f'<span class="highlight-word">"{sc["voice_script"]}"</span>'
            )

            await page.set_content(rendered_html)
            await page.wait_for_timeout(800)
            await page.screenshot(path=frame_img)
            frame_paths.append(frame_img)

        await browser.close()

    # Fast native FFmpeg video assembly
    concat_file = day_dir / "ffmpeg_concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for frame, dur in zip(frame_paths, durations):
            f.write(f"file '{Path(frame).resolve().as_posix()}'\n")
            f.write(f"duration {dur}\n")
        f.write(f"file '{Path(frame_paths[-1]).resolve().as_posix()}'\n")

    out_video = day_dir / "animated_short_day3.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-i", str(master_audio_path),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out_video)
    ]
    print("[Day3 Pipeline] 3. Assembling video via native FFmpeg...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[Day3 Pipeline] ✅ Video rendered: {out_video} ({out_video.stat().st_size} bytes)")
    else:
        print("FFmpeg error:", res.stderr[-1000:])

    # Subtitles SRT
    srt_path = day_dir / "subtitles_day_003.srt"
    generate_subtitles_srt(scenes, durations, srt_path)
    print(f"[Day3 Pipeline] ✅ Complete! Day 3 ready for social video.")

if __name__ == "__main__":
    asyncio.run(render_day3_pipeline())
