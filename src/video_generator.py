import sys
import os
import asyncio
from pathlib import Path
from typing import List, Optional

# Ensure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import edge_tts
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips

class VideoGenerator:
    """Renders 1080x1920 9:16 vertical video YouTube Shorts from AI Series carousels + Andrew Neural TTS."""

    VOICE = "en-US-AndrewMultilingualNeural"
    RATE = "+10%"

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.output_dir = self.base_dir / "AI_SERIES" / "VIDEOS"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def _synthesize_speech(self, script_text: str, output_audio: str):
        communicate = edge_tts.Communicate(script_text, self.VOICE, rate=self.RATE)
        await communicate.save(output_audio)

    def render_short(
        self,
        day: int,
        topic_title: str,
        script_text: str,
        slide_image_paths: List[str]
    ) -> str:
        """
        Creates a synchronized 9:16 vertical short video with voiceover and slide transitions.
        Returns the absolute path to the generated MP4 file.
        """
        day_dir = self.output_dir / f"DAY_{day:03d}"
        day_dir.mkdir(parents=True, exist_ok=True)

        audio_path = str(day_dir / "andrew_voiceover.mp3")
        video_path = str(day_dir / f"short_day_{day:03d}.mp4")

        # 1. Synthesize Voiceover with Andrew
        print(f"[VideoGenerator] Generating Andrew neural voiceover for Day {day:02d}...")
        asyncio.run(self._synthesize_speech(script_text, audio_path))

        # 2. Measure Duration
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        print(f"[VideoGenerator] Voiceover duration: {total_duration:.1f}s")

        # 3. Assemble Slides
        valid_slides = [s for s in slide_image_paths if os.path.exists(s)]
        if not valid_slides:
            raise FileNotFoundError(f"No valid slide images provided for Day {day}")

        slide_duration = total_duration / len(valid_slides)
        print(f"[VideoGenerator] Composing {len(valid_slides)} slides ({slide_duration:.2f}s each)...")

        clips = []
        for s in valid_slides:
            img_clip = ImageClip(str(s)).with_duration(slide_duration)
            clips.append(img_clip)

        final_video = concatenate_videoclips(clips, method="compose")
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
        print(f"[VideoGenerator] ✅ Video rendered: {video_path}")
        return video_path
