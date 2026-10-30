import sys
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import edge_tts
from playwright.sync_api import sync_playwright
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

class VideoGenerator:
    """
    Renders high-production 1080x1920 9:16 vertical animated videos for YouTube Shorts & Instagram Reels.
    Features:
    - Andrew Neural Voice (edge-tts en-US-AndrewMultilingualNeural at +10%)
    - Dynamic visual acts rendered in Playwright Chromium with glowing frosted glass cards
    - Dual Subtitles: Dynamic burned-in on-screen captions + standalone standard .srt subtitle track for YouTube CC
    - Safe-zone optimized layout centered in viewport avoiding mobile overlay obstructions
    """

    VOICE = "en-US-AndrewMultilingualNeural"
    RATE = "+10%"

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.output_dir = self.base_dir / "AI_SERIES" / "VIDEOS"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.template_path = self.base_dir / "src" / "templates" / "animated_short_template.html"

    async def _synthesize_speech(self, script_text: str, output_audio: str):
        communicate = edge_tts.Communicate(script_text, self.VOICE, rate=self.RATE)
        await communicate.save(output_audio)

    def _generate_srt_file(self, scenes: List[Dict[str, Any]], srt_path: str):
        """Builds standard SubRip (.srt) subtitle track for YouTube Captions."""
        def format_timestamp(seconds: float) -> str:
            hrs = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int(round((seconds - int(seconds)) * 1000))
            return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

        srt_blocks = []
        current_time = 0.0
        for i, scene in enumerate(scenes, 1):
            dur = float(scene.get("duration", 10.0))
            start_str = format_timestamp(current_time)
            end_str = format_timestamp(current_time + dur)
            caption = scene.get("caption", "").strip()

            srt_blocks.append(f"{i}\n{start_str} --> {end_str}\n{caption}\n")
            current_time += dur

        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_blocks))
        print(f"[VideoGenerator] Subtitle track created: {srt_path}")

    def render_animated_short(
        self,
        day: int,
        topic_title: str,
        scenes: List[Dict[str, Any]],
        full_narration: str
    ) -> Dict[str, str]:
        """
        Renders a complete animated Short video and matching .srt subtitles.
        Returns dict with paths: {'video_path': ..., 'srt_path': ..., 'audio_path': ...}
        """
        day_dir = self.output_dir / f"DAY_{day:03d}"
        day_dir.mkdir(parents=True, exist_ok=True)
        frames_dir = day_dir / "ANIM_FRAMES"
        frames_dir.mkdir(parents=True, exist_ok=True)

        audio_path = str(day_dir / "narration.mp3")
        video_path = str(day_dir / f"animated_short_day{day}.mp4")
        srt_path = str(day_dir / f"subtitles_day_{day:03d}.srt")

        # 1. Synthesize Voiceover with Andrew
        print(f"[VideoGenerator] Generating Andrew neural voiceover for Day {day:02d}...")
        asyncio.run(self._synthesize_speech(full_narration, audio_path))

        # 2. Generate .srt Closed Captions file
        self._generate_srt_file(scenes, srt_path)

        # 3. Render HTML frames with Playwright
        print(f"[VideoGenerator] Rendering {len(scenes)} visual acts via Chromium...")
        with open(self.template_path, "r", encoding="utf-8") as f:
            html_template = f.read()

        scene_images = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1080, "height": 1920})

            for i, sc in enumerate(scenes):
                act_num = i + 1
                scene_title = sc.get("title", f"Act {act_num}")
                scene_html = sc.get("html", "")
                caption = sc.get("caption", "")
                duration = float(sc.get("duration", 12.0))

                # Inject dynamic scene contents into template
                rendered_html = html_template.replace(
                    '<div class="hero-concept" id="scene-title">Rules-Based Code vs. Learned Behavior</div>',
                    f'<div class="hero-concept" id="scene-title">{scene_title}</div>'
                ).replace(
                    '<div class="stage" id="stage-content">\n    <!-- Populated per scene -->\n  </div>',
                    f'<div class="stage" id="stage-content">\n{scene_html}\n</div>'
                ).replace(
                    '<!-- Dynamic caption text -->',
                    f'<span class="highlight-word">"{caption}"</span>'
                )

                frame_img = str(frames_dir / f"scene_{act_num:02d}.png")
                page.set_content(rendered_html)
                page.wait_for_timeout(800)
                page.screenshot(path=frame_img)
                scene_images.append((frame_img, duration))

            browser.close()

        # 4. Assemble video with MoviePy
        print(f"[VideoGenerator] Assembling video track with audio...")
        clips = []
        for img_path, duration in scene_images:
            clip = ImageClip(img_path).with_duration(duration)
            clips.append(clip)

        final_video = concatenate_videoclips(clips, method="compose")
        audio_clip = AudioFileClip(audio_path)
        final_video = final_video.with_audio(audio_clip)

        print(f"[VideoGenerator] Encoding vertical Short to: {video_path}...")
        final_video.write_videofile(
            video_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            logger=None
        )
        audio_clip.close()
        final_video.close()
        print(f"[VideoGenerator] Done! Short generated: {video_path}")

        return {
            "video_path": video_path,
            "srt_path": srt_path,
            "audio_path": audio_path
        }
