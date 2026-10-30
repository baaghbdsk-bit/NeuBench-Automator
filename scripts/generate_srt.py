import os
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from moviepy import AudioFileClip

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "AI_SERIES" / "VIDEOS" / "DAY_001"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_srt_track(audio_path: str, srt_path: str):
    audio_clip = AudioFileClip(audio_path)
    total_sec = audio_clip.duration
    audio_clip.close()

    cues = [
        (0.0, 12.0, "Most developers think AI is sentient code or mysterious math. In reality, it is simply a fundamental reversal of how we build software."),
        (12.0, 27.0, "In classical programming, developers write explicit rules. Data plus code equals answers. But the moment data shifts, your hardcoded rules crumble!"),
        (27.0, 45.0, "Machine learning flips the entire equation upside down. We supply the data and correct answers, and the algorithm synthesizes the rules for us."),
        (45.0, total_sec, "Rule of thumb: If your problem can be solved with deterministic logic, do not use AI. AI is reserved for high-dimensional, unstructured patterns.")
    ]

    def fmt_time(seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    lines = []
    for i, (start_t, end_t, text) in enumerate(cues, 1):
        lines.append(f"{i}")
        lines.append(f"{fmt_time(start_t)} --> {fmt_time(end_t)}")
        lines.append(text)
        lines.append("")

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[SRT] Generated YouTube subtitle track: {srt_path}")

if __name__ == "__main__":
    audio = str(OUTPUT_DIR / "enriched_andrew.mp3")
    srt = str(OUTPUT_DIR / "subtitles_day_001.srt")
    generate_srt_track(audio, srt)
