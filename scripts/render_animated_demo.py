import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "AI_SERIES" / "VIDEOS" / "DAY_001"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR = OUTPUT_DIR / "ANIM_FRAMES"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

# 4 Key Narrative Acts for Day 1
SCENES = [
    {
        "id": "act1_paradigm",
        "duration": 12.0,
        "title": "The Core Paradigm Shift",
        "caption": "AI is NOT mysterious black-box magic. It is simply an inversion of how code works.",
        "html": """
        <div class="card">
            <div class="card-header">
                <span class="pill pill-green">Mental Model</span>
                <span class="card-title">What is Modern AI?</span>
            </div>
            <div style="font-size: 32px; line-height: 1.5; color: #CBD5E1; margin-bottom: 24px;">
                Traditional software writes deterministic logic.<br>
                Machine learning extracts high-dimensional patterns directly from historical data.
            </div>
            <div class="takeaway">
                💡 <b>The Shift:</b> Moving from human-crafted static rules to continuous mathematical weight optimization.
            </div>
        </div>
        """
    },
    {
        "id": "act2_classical",
        "duration": 15.0,
        "title": "The Classical Trap",
        "caption": "In classical software, developers must hand-code every single edge case. The moment data shifts, your rules break.",
        "html": """
        <div class="card">
            <div class="card-header">
                <span class="pill pill-red">Classical Paradigm</span>
                <span class="card-title">Explicit Logic (Rules)</span>
            </div>
            <div class="flow-box">
                <div class="node">[ Raw Data ]</div>
                <div class="arrow">+</div>
                <div class="node accent">[ Hardcoded Rules ]</div>
                <div class="arrow">➔</div>
                <div class="node">[ Output Answers ]</div>
            </div>
            <div class="code-container">
                <span class="kw">def</span> <span class="fn">detect_spam</span>(email):<br>
                &nbsp;&nbsp;keywords = [<span class="str">"free money"</span>, <span class="str">"click here"</span>]<br>
                &nbsp;&nbsp;<span class="kw">if</span> any(k <span class="kw">in</span> email <span class="kw">for</span> k <span class="kw">in</span> keywords):<br>
                &nbsp;&nbsp;&nbsp;&nbsp;<span class="kw">return</span> <span class="val">True</span><br>
                &nbsp;&nbsp;<span class="com"># Fails on: 'f-r-3-3 m0ney' ❌</span>
            </div>
        </div>
        """
    },
    {
        "id": "act3_ml",
        "duration": 18.0,
        "title": "The Machine Learning Inversion",
        "caption": "Machine learning flips the equation: We supply the data and answers, and the algorithm synthesizes the rules.",
        "html": """
        <div class="card">
            <div class="card-header">
                <span class="pill pill-green">Machine Learning</span>
                <span class="card-title">Pattern Synthesis</span>
            </div>
            <div class="flow-box">
                <div class="node">[ Raw Data ]</div>
                <div class="arrow">+</div>
                <div class="node">[ Correct Answers ]</div>
                <div class="arrow">➔</div>
                <div class="node accent">[ Synthesized Weights ]</div>
            </div>
            <div class="code-container">
                <span class="com"># The model optimizes mathematical parameters</span><br>
                model.<span class="fn">fit</span>(X_train, y_train)<br>
                weights = model.<span class="fn">get_parameters</span>()<br>
                <span class="com"># Automatically captures 'f-r-3-3' & fuzzy variants ✅</span>
            </div>
        </div>
        """
    },
    {
        "id": "act4_takeaway",
        "duration": 12.4,
        "title": "Production Engineering Rule",
        "caption": "If your problem can be solved with static if-else statements, DO NOT use AI. AI is for unstructured, noisy patterns.",
        "html": """
        <div class="card" style="border-color: #38BDF8;">
            <div class="card-header">
                <span class="pill pill-green">Architecture Guide</span>
                <span class="card-title">When Should You Use AI?</span>
            </div>
            <div style="font-size: 32px; line-height: 1.6; color: #F1F5F9; margin-bottom: 24px;">
                ❌ <b>Don't Use AI:</b> Tax calculation, order discounts, deterministic routing.<br><br>
                ✅ <b>Use AI:</b> Computer vision, natural language, semantic search, anomaly detection.
            </div>
            <div class="takeaway">
                📌 <b>Save for revision.</b> Day 2: Symbolic AI vs Statistical Learning!
            </div>
        </div>
        """
    }
]

def render_animated_demo():
    template_path = BASE_DIR / "src" / "templates" / "animated_short_template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    video_output = str(OUTPUT_DIR / "animated_short_day1.mp4")
    audio_path = str(OUTPUT_DIR / "enriched_andrew.mp3")

    print("[AnimatedEngine] Launching Chromium renderer...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1080, "height": 1920})

        scene_images = []
        for i, sc in enumerate(SCENES):
            print(f"[AnimatedEngine] Rendering Scene {i+1}: {sc['title']}...")
            # Inject scene content into template
            rendered_html = html_template.replace(
                '<div class="hero-concept" id="scene-title">Rules-Based Code vs. Learned Behavior</div>',
                f'<div class="hero-concept" id="scene-title">{sc["title"]}</div>'
            ).replace(
                '<div class="stage" id="stage-content">\n    <!-- Populated per scene -->\n  </div>',
                f'<div class="stage" id="stage-content">\n{sc["html"]}\n</div>'
            ).replace(
                '<!-- Dynamic caption text -->',
                f'<span class="highlight-word">"{sc["caption"]}"</span>'
            )

            frame_img = str(FRAMES_DIR / f"scene_{i+1:02d}.png")
            page.set_content(rendered_html)
            page.wait_for_timeout(1000)
            page.screenshot(path=frame_img)
            scene_images.append((frame_img, sc["duration"]))

        browser.close()

    print("[AnimatedEngine] Assembling video with Andrew voiceover...")
    clips = []
    for img_path, duration in scene_images:
        clip = ImageClip(img_path).with_duration(duration)
        clips.append(clip)

    final_video = concatenate_videoclips(clips, method="compose")
    audio_clip = AudioFileClip(audio_path)
    final_video = final_video.with_audio(audio_clip)

    print(f"[AnimatedEngine] Encoding high-bitrate Short to: {video_output}...")
    final_video.write_videofile(
        video_output,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        logger=None
    )
    audio_clip.close()
    final_video.close()
    print(f"[AnimatedEngine] ✅ Production Complete: {video_output}")

if __name__ == "__main__":
    render_animated_demo()
