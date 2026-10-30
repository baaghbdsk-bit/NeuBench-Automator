import subprocess
from pathlib import Path

day_dir = Path("AI_SERIES/VIDEOS/DAY_002")
frames = [day_dir / "ANIM_FRAMES" / f"scene_{i:02d}.png" for i in range(1, 5)]
durations = [14.0, 14.0, 14.0, 14.0]
audio_path = day_dir / "enriched_andrew.mp3"
concat_file = day_dir / "ffmpeg_concat.txt"

with open(concat_file, "w", encoding="utf-8") as f:
    for frame, dur in zip(frames, durations):
        f.write(f"file '{frame.resolve().as_posix()}'\n")
        f.write(f"duration {dur}\n")
    f.write(f"file '{frames[-1].resolve().as_posix()}'\n")

out_video = day_dir / "animated_short_day2.mp4"
cmd = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", str(concat_file),
    "-i", str(audio_path),
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
    "-c:a", "aac", "-b:a", "192k",
    "-shortest",
    str(out_video)
]

print("Assembling video with FFmpeg...")
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode == 0:
    print(f"SUCCESS: Video assembled at {out_video} (Size: {out_video.stat().st_size} bytes)")
else:
    print("FFmpeg error:", res.stderr[-1000:])
