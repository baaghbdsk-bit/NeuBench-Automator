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

    def generate_dynamic_short(self, topic_data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Optional[str]]:
        """
        Dynamically renders a vertical animated Short/Reel (1080x1920) with voiceover and captions.
        Gracefully falls back to autonomous visual engine MP4 if audio/rendering pipeline fails.
        """
        import re
        title = topic_data.get("title", "AI Breakthrough")
        category = topic_data.get("category", "SYSTEMS").upper()
        summary = topic_data.get("summary", "Understanding modern artificial intelligence systems.")
        problem = topic_data.get("problem", "Traditional models run into severe compute bottlenecks.")
        solution = topic_data.get("solution", "Dynamic routing and memory optimization accelerate throughput.")
        pro_tip = topic_data.get("pro_tip", "Always benchmark real latency on live workloads.")
        narration = topic_data.get("narration", f"{title}. {summary}. The key breakthrough is {solution}. Benchmarked live on NeuBench.")

        slug = re.sub(r'[^a-zA-Z0-9]+', '_', title.lower()).strip('_')[:40]
        video_dir = self.base_dir / "generated_visuals" / "videos" / slug
        video_dir.mkdir(parents=True, exist_ok=True)
        frames_dir = video_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        audio_path = str(video_dir / "narration.mp3")
        video_path = str(video_dir / f"short_{slug}.mp4")
        srt_path = str(video_dir / f"subtitles_{slug}.srt")

        if dry_run:
            if not Path(video_path).exists():
                Path(video_path).touch()
            return {
                "video_path": video_path,
                "srt_path": srt_path,
                "audio_path": audio_path
            }

        scenes = [
            {
                "title": f"{category} • {title}",
                "caption": f"Why {title} changes modern AI systems",
                "duration": 8.0,
                "html": f"""
                <div style="background: rgba(15,23,42,0.85); border: 2px solid #38BDF8; border-radius: 24px; padding: 40px; margin-top: 100px;">
                  <div style="font-size: 28px; color: #38BDF8; font-weight: 700; margin-bottom: 20px;">⚡ CONCEPT BREAKTHROUGH</div>
                  <div style="font-size: 44px; font-weight: 800; color: #FFFFFF; line-height: 1.3;">{title}</div>
                  <div style="font-size: 30px; color: #CBD5E1; margin-top: 25px; line-height: 1.5;">{summary}</div>
                </div>
                """
            },
            {
                "title": "The Bottleneck",
                "caption": "Why standard brute-force scaling fails",
                "duration": 10.0,
                "html": f"""
                <div style="background: rgba(15,23,42,0.85); border: 2px solid #FB7185; border-radius: 24px; padding: 40px; margin-top: 100px;">
                  <div style="font-size: 28px; color: #FB7185; font-weight: 700; margin-bottom: 20px;">⚠️ THE CORE BOTTLENECK</div>
                  <div style="font-size: 34px; color: #F1F5F9; line-height: 1.6;">{problem}</div>
                </div>
                """
            },
            {
                "title": "The Mechanism",
                "caption": "The engineering solution unlocked",
                "duration": 10.0,
                "html": f"""
                <div style="background: rgba(15,23,42,0.85); border: 2px solid #34D399; border-radius: 24px; padding: 40px; margin-top: 100px;">
                  <div style="font-size: 28px; color: #34D399; font-weight: 700; margin-bottom: 20px;">💡 HOW IT WORKS</div>
                  <div style="font-size: 34px; color: #F1F5F9; line-height: 1.6;">{solution}</div>
                </div>
                """
            },
            {
                "title": "Key Takeaway",
                "caption": "Track continuous live evals on NeuBench",
                "duration": 8.0,
                "html": f"""
                <div style="background: rgba(15,23,42,0.85); border: 2px solid #818CF8; border-radius: 24px; padding: 40px; margin-top: 100px; text-align: center;">
                  <div style="font-size: 28px; color: #818CF8; font-weight: 700; margin-bottom: 20px;">📊 PRODUCTION RULE</div>
                  <div style="font-size: 32px; color: #F8FAFC; line-height: 1.6; margin-bottom: 30px;">{pro_tip}</div>
                  <div style="font-size: 26px; color: #38BDF8; font-weight: 700;">Live benchmarks on neubench.netlify.app</div>
                </div>
                """
            }
        ]

        try:
            # 1. Synthesize voiceover with 15s timeout
            async def _timed_synth():
                await self._synthesize_speech(narration, audio_path)
            asyncio.run(asyncio.wait_for(_timed_synth(), timeout=15.0))

            # 2. Build SRT
            self._generate_srt_file(scenes, srt_path)

            # 3. Render frames with Playwright
            with open(self.template_path, "r", encoding="utf-8") as f:
                html_template = f.read()

            scene_images = []
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1080, "height": 1920})
                for i, sc in enumerate(scenes):
                    act_num = i + 1
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
                    frame_img = str(frames_dir / f"scene_{act_num:02d}.png")
                    page.set_content(rendered_html)
                    page.wait_for_timeout(600)
                    page.screenshot(path=frame_img)
                    scene_images.append((frame_img, sc["duration"]))
                browser.close()

            # 4. Assemble video with MoviePy
            clips = [ImageClip(img_path).with_duration(dur) for img_path, dur in scene_images]
            final_video = concatenate_videoclips(clips, method="compose")
            audio_clip = AudioFileClip(audio_path)
            final_video = final_video.with_audio(audio_clip)
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
            return {
                "video_path": video_path,
                "srt_path": srt_path,
                "audio_path": audio_path
            }
        except Exception as e:
            print(f"[VideoGenerator] Primary render note: {e}. Falling back to visual engine MP4.")
            try:
                from src.autonomous_visual_engine import generate_visual_for_post
                _gif, fallback_mp4 = generate_visual_for_post(title, summary)
                if fallback_mp4 and Path(fallback_mp4).exists():
                    return {
                        "video_path": str(fallback_mp4),
                        "srt_path": None,
                        "audio_path": None
                    }
            except Exception as fb_err:
                print(f"[VideoGenerator] Visual engine fallback error: {fb_err}")

        return {"video_path": None, "srt_path": None, "audio_path": None}
