import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

OUTPUT_DIR = Path("generated_visuals")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def convert_mp4_to_gif(mp4_path: str, gif_path: str, fps: int = 12, width: int = 800) -> bool:
    """Converts MP4 to high-quality looping GIF via ffmpeg."""
    try:
        vf = f"fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        cmd = ["ffmpeg", "-y", "-i", mp4_path, "-vf", vf, gif_path]
        res = subprocess.run(cmd, capture_output=True, timeout=30)
        if res.returncode == 0 and Path(gif_path).exists() and Path(gif_path).stat().st_size > 0:
            return True
    except Exception as e:
        print(f"[ManimRenderer] ffmpeg palette conversion note: {e}")

    # Fallback simpler conversion
    try:
        cmd = ["ffmpeg", "-y", "-i", mp4_path, "-vf", f"fps={fps},scale={width}:-1", gif_path]
        res = subprocess.run(cmd, capture_output=True, timeout=20)
        return res.returncode == 0 and Path(gif_path).exists() and Path(gif_path).stat().st_size > 0
    except Exception as e:
        print(f"[ManimRenderer] ffmpeg fallback conversion failed: {e}")
        return False


def render_scene(
    scene_module: str,
    scene_class: str,
    output_name: str,
    spec: Optional[Dict[str, Any]] = None
) -> Tuple[str, str]:
    """
    Renders a Manim scene in 1080x1080 square format with NeuBench dark mode theme.
    Returns (mp4_path, gif_path).
    """
    target_mp4 = OUTPUT_DIR / f"{output_name}.mp4"
    target_gif = OUTPUT_DIR / f"{output_name}.gif"

    # Write spec file if provided so the scene can read dynamic parameters
    spec_path = OUTPUT_DIR / f"{output_name}_spec.json"
    env = os.environ.copy()
    if spec:
        try:
            with open(spec_path, "w", encoding="utf-8") as f:
                json.dump(spec, f, ensure_ascii=False, indent=2)
            env["MANIM_SPEC_PATH"] = str(spec_path.resolve())
        except Exception as e:
            print(f"[ManimRenderer] Could not write spec json: {e}")

    # Run Manim CLI
    # -ql: fast low-quality 15fps render (renders in ~2-3s)
    # -r 1080,1080: 1:1 square aspect ratio for X and omnichannel social feeds
    media_dir = Path("media")
    cmd = [
        sys.executable, "-m", "manim",
        "-ql",
        "-r", "1080,1080",
        "--media_dir", str(media_dir),
        "-o", output_name,
        f"src/{scene_module}.py",
        scene_class
    ]

    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            print(f"[ManimRenderer] Manim stderr: {proc.stderr[:400]}")
    except Exception as err:
        print(f"[ManimRenderer] Subprocess error running Manim: {err}")

    # Search for rendered MP4 in media directories
    found_mp4 = None
    candidate_paths = [
        media_dir / "videos" / scene_module / "1080p15" / f"{output_name}.mp4",
        media_dir / "videos" / scene_module / "1080p15" / f"{scene_class}.mp4",
        media_dir / "videos" / scene_module / "480p15" / f"{output_name}.mp4",
        media_dir / "videos" / scene_module / "480p15" / f"{scene_class}.mp4",
    ]
    for p in candidate_paths:
        if p.exists() and p.stat().st_size > 0:
            found_mp4 = p
            break

    if not found_mp4:
        for p in media_dir.glob(f"**/{output_name}.mp4"):
            if p.exists() and p.stat().st_size > 0:
                found_mp4 = p
                break

    if found_mp4:
        shutil.copy2(found_mp4, target_mp4)
    else:
        print(f"[ManimRenderer] Warning: Could not locate rendered MP4 for {output_name}")

    # Generate looping GIF
    if target_mp4.exists() and target_mp4.stat().st_size > 0:
        convert_mp4_to_gif(str(target_mp4), str(target_gif))

    return str(target_mp4), str(target_gif)
