import subprocess
from pathlib import Path


def convert_mp4_to_gif(mp4_path: str, gif_path: str, fps: int = 12, width: int = 800) -> bool:
    """Converts MP4 to high-quality looping GIF via ffmpeg."""
    try:
        vf = f"fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        cmd = ["ffmpeg", "-y", "-i", mp4_path, "-vf", vf, gif_path]
        res = subprocess.run(cmd, capture_output=True, timeout=30)
        if res.returncode == 0 and Path(gif_path).exists() and Path(gif_path).stat().st_size > 0:
            return True
    except Exception as e:
        print(f"[FFmpegUtils] ffmpeg palette conversion note: {e}")

    try:
        cmd = ["ffmpeg", "-y", "-i", mp4_path, "-vf", f"fps={fps},scale={width}:-1", gif_path]
        res = subprocess.run(cmd, capture_output=True, timeout=20)
        return res.returncode == 0 and Path(gif_path).exists() and Path(gif_path).stat().st_size > 0
    except Exception as e:
        print(f"[FFmpegUtils] ffmpeg fallback conversion failed: {e}")
        return False
