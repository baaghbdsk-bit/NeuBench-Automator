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

    def _get_audio_duration(self, audio_path: str) -> float:
        """Determines the duration in seconds of the synthesized audio file."""
        import subprocess, json
        try:
            res = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(audio_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            if res.returncode == 0:
                data = json.loads(res.stdout)
                return float(data.get("format", {}).get("duration", 36.0))
        except Exception:
            pass
        return 36.0

    def _assemble_video_ffmpeg(self, scene_images: List[Any], audio_path: str, output_path: str) -> bool:
        """
        High-performance direct FFmpeg assembly.
        Renders multi-scene vertical 1080x1920 video with voiceover in seconds.
        """
        import subprocess
        concat_file = Path(output_path).parent / "concat_list.txt"
        try:
            with open(concat_file, "w", encoding="utf-8") as f:
                for img_path, duration in scene_images:
                    p_str = Path(img_path).resolve().as_posix()
                    f.write(f"file '{p_str}'\n")
                    f.write(f"duration {duration:.2f}\n")
                if scene_images:
                    last_img = Path(scene_images[-1][0]).resolve().as_posix()
                    f.write(f"file '{last_img}'\n")

            total_scene_dur = min(sum(dur for _, dur in scene_images), 58.0) if scene_images else 55.0

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-i", str(audio_path),
                "-t", f"{total_scene_dur:.2f}",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-preset", "ultrafast",
                "-r", "24",
                str(output_path)
            ]

            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
            if proc.returncode != 0:
                print(f"[VideoGenerator] FFmpeg error: {proc.stderr[:300]}")
                return False
            return Path(output_path).exists() and Path(output_path).stat().st_size > 50000
        except Exception as ex:
            print(f"[VideoGenerator] FFmpeg execution exception: {ex}")
            return False
        finally:
            if concat_file.exists():
                try:
                    concat_file.unlink()
                except Exception:
                    pass

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

        # 4. Assemble video with FFmpeg
        print(f"[VideoGenerator] Assembling video track with audio via FFmpeg...")
        assembled = self._assemble_video_ffmpeg(scene_images, audio_path, video_path)
        if not assembled:
            print(f"[VideoGenerator] FFmpeg assembly fallback to MoviePy...")
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
        Dynamically renders a full-duration vertical animated Short/Reel (1080x1920) with voiceover and captions.
        Uses direct FFmpeg rendering for maximum speed and reliability.
        """
        import re
        title = topic_data.get("title", "AI Breakthrough")
        category = topic_data.get("category", "SYSTEMS").upper()
        summary = topic_data.get("summary", "Understanding modern artificial intelligence systems.")
        problem = topic_data.get("problem", "Traditional models run into severe compute bottlenecks.")
        solution = topic_data.get("solution", "Dynamic routing and memory optimization accelerate throughput.")
        pro_tip = topic_data.get("pro_tip", "Always benchmark real latency on live workloads.")
        narration = topic_data.get("narration")
        if not narration or len(narration.split()) < 60:
            narration = (
                f"In this engineering breakdown, we analyze {title}. "
                f"{summary}. "
                f"Why does this matter so much for production deployments? "
                f"Under conventional architectures, {problem}. As batch throughput scales, memory transfer creates a severe latency bottleneck. "
                f"The core technical unlock is {solution}. This achieves dramatic acceleration without degrading precision. "
                f"Here is your production engineering rule: {pro_tip}. "
                f"To inspect live latency, memory, and token economics across 260-plus frontier models, explore NeuBench at neubench.netlify.app."
            )

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
            # 1. Synthesize voiceover with 60s timeout
            async def _timed_synth():
                await self._synthesize_speech(narration, audio_path)
            asyncio.run(asyncio.wait_for(_timed_synth(), timeout=60.0))

            # 2. Match scene durations to synthesized audio length (targeting 50-60s)
            audio_dur = self._get_audio_duration(audio_path)
            total_dur = min(max(audio_dur, 48.0), 59.0)
            d1 = round(total_dur * 0.22, 1)
            d2 = round(total_dur * 0.28, 1)
            d3 = round(total_dur * 0.28, 1)
            d4 = round(total_dur - (d1 + d2 + d3), 1)
            scenes[0]["duration"] = d1
            scenes[1]["duration"] = d2
            scenes[2]["duration"] = d3
            scenes[3]["duration"] = d4

            # 3. Build SRT matching precise timing
            self._generate_srt_file(scenes, srt_path)

            # 4. Render frames with Playwright
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

            # 5. Fast FFmpeg assembly with MoviePy fallback
            assembled = self._assemble_video_ffmpeg(scene_images, audio_path, video_path)
            if not assembled:
                print("[VideoGenerator] FFmpeg failed, falling back to MoviePy...")
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

            if Path(video_path).exists() and Path(video_path).stat().st_size > 50000:
                print(f"[VideoGenerator] ✅ Dynamic Short assembled successfully: {video_path}")
                return {
                    "video_path": video_path,
                    "srt_path": srt_path,
                    "audio_path": audio_path
                }
        except Exception as e:
            print(f"[VideoGenerator] Dynamic short render error: {e}")

        return {"video_path": None, "srt_path": None, "audio_path": None}
