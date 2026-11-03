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

DAY_4_CONTENT = {
    "day": 4,
    "topic": "What is a Dataset? (Inputs, Targets, and Why Data Quality Trumps Code)",
    "level": "Level 1: AI Fundamentals",
    "scenes": [
        {
            "id": "act1_foundation",
            "title": "What is a Dataset?",
            "voice_script": "A machine learning model is an empty shell with zero intelligence until it is trained on a dataset. Datasets are not just tables of numbers, they are the actual code that writes the model's weights.",
            "html": """
            <div class="card">
                <div class="card-header">
                    <span class="pill pill-blue">The Core Concept</span>
                    <span class="card-title">Datasets are the Code</span>
                </div>
                <div style="font-size: 32px; line-height: 1.5; color: #CBD5E1; margin-bottom: 24px;">
                    In traditional software, human developers write <b>logic</b>.<br>
                    In machine learning, <b>data writes the logic</b>. The model is merely a blank function approximator waiting for numbers.
                </div>
                <div class="takeaway">
                    💡 <b>The Law:</b> Data quality dictates model behavior far more than model architecture.
                </div>
            </div>
            """
        },
        {
            "id": "act2_inputs_targets",
            "title": "Inputs (X) vs. Targets (Y)",
            "voice_script": "Every supervised dataset consists of pairs: inputs called X and ground truth targets called Y. The model observes X and tries to guess Y correctly across millions of examples.",
            "html": """
            <div class="card">
                <div class="card-header">
                    <span class="pill pill-purple">The Fundamental Pair</span>
                    <span class="card-title">Inputs (X) vs. Targets (Y)</span>
                </div>
                <div style="display: flex; gap: 20px; margin-bottom: 24px;">
                    <div style="flex: 1; background: rgba(56, 189, 248, 0.08); border: 1.5px solid rgba(56, 189, 248, 0.3); border-radius: 16px; padding: 24px;">
                        <div style="color: #38BDF8; font-weight: 800; font-size: 26px; margin-bottom: 12px;">📥 Features (X)</div>
                        <div style="font-size: 24px; color: #E2E8F0; line-height: 1.5;">The observed signals: pixels, audio, tokens, or tabular metrics.</div>
                    </div>
                    <div style="flex: 1; background: rgba(52, 211, 153, 0.08); border: 1.5px solid rgba(52, 211, 153, 0.3); border-radius: 16px; padding: 24px;">
                        <div style="color: #34D399; font-weight: 800; font-size: 26px; margin-bottom: 12px;">🎯 Target (Y)</div>
                        <div style="font-size: 24px; color: #E2E8F0; line-height: 1.5;">The ground truth: price, sentiment label, diagnosis, or next token.</div>
                    </div>
                </div>
                <div class="takeaway" style="border-color: rgba(56, 189, 248, 0.4);">
                    📌 <b>Dataset Anatomy:</b> Every training sample is a structured tuple (X, Y).
                </div>
            </div>
            """
        },
        {
            "id": "act3_gigo",
            "title": "Garbage In, Garbage Out",
            "voice_script": "If you feed a multi-billion parameter neural network corrupted or mislabeled data, it learns to hallucinate mistakes with absolute mathematical confidence. Clean data trumps model size every time.",
            "html": """
            <div class="card">
                <div class="card-header">
                    <span class="pill pill-orange">The Golden Rule</span>
                    <span class="card-title">Garbage In, Garbage Out</span>
                </div>
                <div style="font-size: 30px; line-height: 1.5; color: #CBD5E1; margin-bottom: 24px;">
                    A small model trained on pristine, curated data will reliably beat a giant model trained on noisy web scrapes.
                </div>
                <div class="code-box">
Corrupted Data  ➔ High Loss ➔ Persistent Hallucinations
Curated Data    ➔ Rapid Convergence ➔ Production Generalization
                </div>
                <div class="takeaway" style="border-color: rgba(251, 146, 60, 0.4);">
                    🔥 <b>Data-Centric AI:</b> Spend 80% of engineering time curating data, not tweaking hyper-parameters.
                </div>
            </div>
            """
        },
        {
            "id": "act4_recap",
            "title": "Day 04 Cheatsheet & Summary",
            "voice_script": "Datasets are the curriculum your AI studies. Tomorrow in Day five, we break down features and labels in modern engineering. Follow NeuBench for the complete ninety-day AI masterclass.",
            "html": """
            <div class="card">
                <div class="card-header">
                    <span class="pill pill-green">Day 04 Cheatsheet</span>
                    <span class="card-title">Summary Checklist</span>
                </div>
                <div style="font-size: 28px; line-height: 1.6; color: #F1F5F9; display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px;">
                    <div>1️⃣ <b>Datasets are the Code:</b> Data writes the neural weights directly.</div>
                    <div>2️⃣ <b>Inputs (X) & Labels (Y):</b> Observations mapped to ground-truth answers.</div>
                    <div>3️⃣ <b>Quality Over Quantity:</b> High-signal data prevents hallucinations.</div>
                </div>
                <div class="takeaway" style="background: rgba(34, 211, 238, 0.1); border-color: #22D3EE; text-align: center;">
                    ⚡ <b>Tomorrow (Day 05):</b> Features & Labels: Real-World Problems into Numbers.
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

async def render_day4_pipeline():
    day_dir = VIDEOS_DIR / "DAY_004"
    frames_dir = day_dir / "ANIM_FRAMES"
    day_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    scenes = DAY_4_CONTENT["scenes"]
    template_path = BASE_DIR / "src" / "templates" / "animated_short_template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    print("[Day4 Pipeline] 1. Generating Andrew Neural voiceovers...")
    durations = [14.0, 14.0, 14.0, 14.0]
    full_script = " ".join([sc["voice_script"] for sc in scenes])
    master_audio_path = day_dir / "enriched_andrew.mp3"
    tts = edge_tts.Communicate(full_script, "en-US-AndrewMultilingualNeural", rate="+3%")
    await tts.save(str(master_audio_path))
    print(f"[Day4 Pipeline] Audio saved to {master_audio_path}")

    print("[Day4 Pipeline] 2. Rendering high-res frames with Safe-Zone padding...")
    frame_paths = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})

        for i, sc in enumerate(scenes):
            frame_img = str(frames_dir / f"scene_{i+1:02d}.png")
            print(f"  -> Rendering Scene {i+1}: {sc['title']}...")

            rendered_html = html_template.replace(
                '<div class="series-tag">AI Explained • Day 01</div>',
                '<div class="series-tag">AI Explained • Day 04</div>'
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

    out_video = day_dir / "animated_short_day4.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-i", str(master_audio_path),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(out_video)
    ]
    print("[Day4 Pipeline] 3. Assembling video via native FFmpeg...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[Day4 Pipeline] ✅ Video rendered: {out_video} ({out_video.stat().st_size} bytes)")
    else:
        print("FFmpeg error:", res.stderr[-1000:])

    # Subtitles SRT
    srt_path = day_dir / "subtitles_day_004.srt"
    generate_subtitles_srt(scenes, durations, srt_path)
    print(f"[Day4 Pipeline] ✅ Complete! Day 4 ready for YouTube Shorts and Instagram Reels.")

if __name__ == "__main__":
    asyncio.run(render_day4_pipeline())
