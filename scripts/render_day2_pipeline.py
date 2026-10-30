import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import edge_tts
from playwright.async_api import async_playwright
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = BASE_DIR / "AI_SERIES" / "VIDEOS"

DAY_2_CONTENT = {
    "day": 2,
    "topic": "AI vs. Machine Learning vs. Deep Learning",
    "level": "Level 1: AI Fundamentals",
    "scenes": [
        {
            "id": "act1_hierarchy",
            "title": "The Russian Doll Hierarchy",
            "voice_script": "Most people use AI, machine learning, and deep learning as buzzwords interchangeably. But mathematically, they represent three concentric circles nested like Russian nesting dolls.",
            "card_tag": "The Mental Model",
            "tag_color": "pill-blue",
            "html": """
            <div class="card">
                <div class="card-header">
                    <span class="pill pill-blue">The Mental Model</span>
                    <span class="card-title">Three Concentric Circles</span>
                </div>
                <div style="font-size: 32px; line-height: 1.5; color: #CBD5E1; margin-bottom: 24px;">
                    <b>Artificial Intelligence</b> is the broad umbrella of machine intelligence.<br>
                    <b>Machine Learning</b> is the subset that learns from data without explicit rules.<br>
                    <b>Deep Learning</b> is the specialized subset using multi-layer neural networks.
                </div>
                <div class="takeaway">
                    💡 <b>The Rule:</b> All Deep Learning is Machine Learning. All Machine Learning is AI. But NOT all AI is Deep Learning.
                </div>
            </div>
            """
        },
        {
            "id": "act2_classical_vs_ml",
            "title": "AI vs Machine Learning",
            "voice_script": "Artificial intelligence started in the nineteen fifties with symbolic logic and expert systems. If you write ten thousand if-else statements for chess, you have built AI, but you have zero machine learning.",
            "card_tag": "The Grand Distinction",
            "tag_color": "pill-purple",
            "html": """
            <div class="card">
                <div class="card-header">
                    <span class="pill pill-purple">The Grand Distinction</span>
                    <span class="card-title">Symbolic AI vs. ML</span>
                </div>
                <div style="display: flex; gap: 20px; margin-bottom: 24px;">
                    <div style="flex: 1; background: rgba(255,255,255,0.04); border: 1.5px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px;">
                        <div style="color: #38BDF8; font-weight: 800; font-size: 26px; margin-bottom: 12px;">Symbolic AI (1950s)</div>
                        <div style="font-size: 24px; color: #94A3B8; line-height: 1.5;">Humans write all rules & edge cases. Brittle and cannot adapt to novel scenarios.</div>
                    </div>
                    <div style="flex: 1; background: rgba(52, 211, 153, 0.08); border: 1.5px solid rgba(52, 211, 153, 0.3); border-radius: 16px; padding: 24px;">
                        <div style="color: #34D399; font-weight: 800; font-size: 26px; margin-bottom: 12px;">Machine Learning (1990s)</div>
                        <div style="font-size: 24px; color: #E2E8F0; line-height: 1.5;">Algorithms adjust numerical weights directly from raw dataset patterns.</div>
                    </div>
                </div>
                <div class="takeaway" style="border-color: rgba(56, 189, 248, 0.4);">
                    📌 <b>Key Takeaway:</b> Deep Blue beating Kasparov was Symbolic AI. AlphaGo was Deep Reinforcement Learning.
                </div>
            </div>
            """
        },
        {
            "id": "act3_dl_breakthrough",
            "title": "Why Deep Learning Dominated",
            "voice_script": "Traditional machine learning required human engineers to spend months crafting features by hand. Deep learning obliterated that bottleneck by learning hierarchical representations directly from raw pixels and text.",
            "card_tag": "The Feature Bottleneck",
            "tag_color": "pill-orange",
            "html": """
            <div class="card">
                <div class="card-header">
                    <span class="pill pill-orange">The Feature Bottleneck</span>
                    <span class="card-title">Feature Engineering vs Deep Layers</span>
                </div>
                <div style="font-size: 30px; line-height: 1.5; color: #CBD5E1; margin-bottom: 24px;">
                    Traditional ML capped out when datasets grew massive.<br>
                    Deep Neural Networks possess the capacity to absorb billions of parameters without plateauing.
                </div>
                <div class="code-box">
Traditional ML:  [Raw Input] ➔ [Human Manual Feature Engineering] ➔ [Classifier]
Deep Learning:   [Raw Input] ➔ [Layer 1] ➔ [Layer 2] ➔ [Layer N] ➔ [Prediction]
                </div>
                <div class="takeaway" style="border-color: rgba(251, 146, 60, 0.4);">
                    🔥 <b>The Breakthrough:</b> Neural networks don't just learn decisions, they learn what representations matter.
                </div>
            </div>
            """
        },
        {
            "id": "act4_summary_cta",
            "title": "Day 02 Takeaway & Summary",
            "voice_script": "Remember this rule of thumb: When someone says AI today, they usually mean Deep Learning. Tomorrow in Day three, we uncover how computers actually learn functions. Follow NeuBench for the complete ninety-day journey.",
            "card_tag": "Day 02 Cheatsheet",
            "tag_color": "pill-green",
            "html": """
            <div class="card">
                <div class="card-header">
                    <span class="pill pill-green">Day 02 Cheatsheet</span>
                    <span class="card-title">Core Mental Framework</span>
                </div>
                <div style="font-size: 28px; line-height: 1.6; color: #F1F5F9; display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px;">
                    <div>1️⃣ <b>AI:</b> Any machine exhibiting human-like reasoning or logic.</div>
                    <div>2️⃣ <b>ML:</b> Probabilistic statistical models trained on data.</div>
                    <div>3️⃣ <b>DL:</b> Deep neural nets that automatically discover features.</div>
                </div>
                <div class="takeaway" style="background: rgba(34, 211, 238, 0.1); border-color: #22D3EE; text-align: center;">
                    ⚡ <b>Tomorrow (Day 03):</b> How Computers Actually Learn (Function Approximation).
                </div>
            </div>
            """
        }
    ]
}

def generate_subtitles_srt(scenes: List[Dict[str, Any]], durations: List[float], srt_path: Path):
    """Generates a standard .srt subtitle file from the scene voice scripts and measured audio durations."""
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
    print(f"[Subtitles] SRT captions saved: {srt_path}")

async def render_day2_pipeline():
    day_dir = VIDEOS_DIR / "DAY_002"
    frames_dir = day_dir / "ANIM_FRAMES"
    day_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    scenes = DAY_2_CONTENT["scenes"]
    template_path = BASE_DIR / "src" / "templates" / "animated_short_template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    print("[Day2 Pipeline] 1. Generating Andrew Neural voiceovers per scene...")
    scene_audio_files = []
    durations = []

    for i, sc in enumerate(scenes):
        act_audio = day_dir / f"act_{i+1:02d}_andrew.mp3"
        print(f"  -> Synthesizing Act {i+1} audio...")
        tts = edge_tts.Communicate(sc["voice_script"], "en-US-AndrewMultilingualNeural", rate="+3%")
        await tts.save(str(act_audio))
        scene_audio_files.append(str(act_audio))

        # Get exact audio duration
        clip = AudioFileClip(str(act_audio))
        durations.append(clip.duration + 0.5) # add 0.5s breathing room
        clip.close()

    print(f"[Day2 Pipeline] Total narration duration: {sum(durations):.1f}s")

    # Render visual frames
    print("[Day2 Pipeline] 2. Rendering high-res frames via Playwright...")
    frame_paths = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})

        for i, sc in enumerate(scenes):
            frame_img = str(frames_dir / f"scene_{i+1:02d}.png")
            print(f"  -> Rendering Scene {i+1}: {sc['title']}...")

            rendered_html = html_template.replace(
                '<div class="series-tag">AI Explained • Day 01</div>',
                '<div class="series-tag">AI Explained • Day 02</div>'
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

    # Concatenate audio
    print("[Day2 Pipeline] 3. Assembling audio & video clips...")
    combined_audio_clips = [AudioFileClip(a) for a in scene_audio_files]
    full_audio = concatenate_audioclips(combined_audio_clips)
    master_audio_path = str(day_dir / "enriched_andrew.mp3")
    full_audio.write_audiofile(master_audio_path, logger=None)

    # Video assembly
    video_clips = []
    for f_path, dur in zip(frame_paths, durations):
        v_clip = ImageClip(f_path).with_duration(dur)
        video_clips.append(v_clip)

    final_video = concatenate_videoclips(video_clips, method="compose")
    final_audio_clip = AudioFileClip(master_audio_path)
    final_video = final_video.with_audio(final_audio_clip)

    video_output = str(day_dir / "animated_short_day2.mp4")
    print(f"[Day2 Pipeline] 4. Encoding 1080x1920 MP4 to {video_output}...")
    final_video.write_videofile(
        video_output,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        logger=None
    )

    final_audio_clip.close()
    for ac in combined_audio_clips:
        ac.close()
    final_video.close()

    # Generate subtitles SRT
    srt_path = day_dir / "subtitles_day_002.srt"
    generate_subtitles_srt(scenes, durations, srt_path)

    print(f"[Day2 Pipeline] ✅ SUCCESS: Day 2 short produced at: {video_output}")
    return video_output, str(srt_path)

if __name__ == "__main__":
    asyncio.run(render_day2_pipeline())
