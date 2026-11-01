"""
NeuBench Animated Visual Generator (PIL + FFmpeg).
Generates high-resolution 1080x1080 animated MP4 loops and GIFs for LinkedIn posts.
Renders real-time AI model benchmark races (TTFT vs TPS) with glowing neon visual aesthetics.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent

# Color Palette: Modern Dark Mode Engineering Theme
BG_COLOR = (10, 14, 23)          # Deep Midnight Blue
CARD_BG = (17, 24, 39)           # Dark Slate Container
TEXT_WHITE = (248, 250, 252)     # High-contrast White
TEXT_MUTED = (148, 163, 184)     # Slate 400
BORDER_COLOR = (30, 41, 59)      # Slate 800

# Benchmark Competitors & Neon Brand Accents
MODELS = [
    {"name": "DeepSeek-V3", "provider": "DeepSeek API", "tps": 114, "ttft_ms": 210, "color": (59, 130, 246)},    # Vibrant Blue
    {"name": "Claude 3.5 Sonnet", "provider": "Anthropic", "tps": 82, "ttft_ms": 280, "color": (217, 119, 6)},   # Warm Amber
    {"name": "GPT-4o", "provider": "OpenAI", "tps": 96, "ttft_ms": 240, "color": (16, 185, 129)},               # Emerald Green
    {"name": "Llama 3.3 70B", "provider": "Together AI", "tps": 128, "ttft_ms": 175, "color": (168, 85, 247)},    # Purple
    {"name": "Gemini 2.0 Flash", "provider": "Google Cloud", "tps": 142, "ttft_ms": 140, "color": (236, 72, 153)} # Hot Pink
]

def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Loads a high-quality system font or falls back to default."""
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahomabd.ttf" if bold else "C:/Windows/Fonts/tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def render_benchmark_animation(
    output_mp4: Path,
    title: str = "Real-World LLM Inference Speed & Latency",
    subtitle: str = "Live Tokens/Sec (TPS) & Time to First Token (TTFT) • NeuBench Lab",
    fps: int = 24,
    duration_sec: float = 3.5
) -> Optional[Path]:
    """
    Renders an animated 1080x1080 MP4 video displaying animated benchmark bars
    and live counter tickers.
    """
    output_mp4 = Path(output_mp4)
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    temp_frames_dir = output_mp4.parent / "_temp_frames"
    if temp_frames_dir.exists():
        shutil.rmtree(temp_frames_dir)
    temp_frames_dir.mkdir(parents=True, exist_ok=True)

    width, height = 1080, 1080
    total_frames = int(fps * duration_sec)
    max_tps = max(m["tps"] for m in MODELS)

    font_brand = get_font(26, bold=True)
    font_title = get_font(42, bold=True)
    font_sub = get_font(22, bold=False)
    font_label = get_font(26, bold=True)
    font_meta = get_font(18, bold=False)
    font_val = get_font(24, bold=True)
    font_footer = get_font(22, bold=True)

    print(f"[VisualAnimator] Rendering {total_frames} frames ({duration_sec}s @ {fps}fps)...")

    for frame_idx in range(total_frames):
        # Progress: 0.0 -> 1.0 (with ease-out curve for natural deceleration)
        t = frame_idx / float(total_frames - 1)
        # Ease-out cubic: 1 - (1 - t)^3
        progress = 1.0 - (1.0 - t) ** 3

        img = Image.new("RGB", (width, height), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # 1. Subtle Background Grid Pattern
        for x in range(0, width, 60):
            draw.line([(x, 0), (x, height)], fill=(16, 22, 34), width=1)
        for y in range(0, height, 60):
            draw.line([(0, y), (width, y)], fill=(16, 22, 34), width=1)

        # 2. Header Container
        draw.rounded_rectangle([(60, 50), (1020, 210)], radius=16, fill=CARD_BG, outline=BORDER_COLOR, width=2)
        
        # NeuBench Badge
        draw.rounded_rectangle([(90, 75), (290, 115)], radius=8, fill=(30, 41, 59), outline=(51, 65, 85), width=1)
        draw.text((105, 82), "⚡ NEUBENCH LIVE", font=font_brand, fill=(56, 189, 248))
        draw.ellipse([(268, 91), (278, 101)], fill=(34, 197, 94)) # Glowing green online dot

        # Title & Subtitle
        draw.text((90, 125), title, font=font_title, fill=TEXT_WHITE)
        draw.text((90, 175), subtitle, font=font_sub, fill=TEXT_MUTED)

        # 3. Benchmark Bar Items
        start_y = 250
        bar_height = 92
        spacing = 30
        max_bar_width = 540

        for i, model in enumerate(MODELS):
            y = start_y + i * (bar_height + spacing)
            
            # Card background
            draw.rounded_rectangle([(60, y), (1020, y + bar_height)], radius=14, fill=CARD_BG, outline=BORDER_COLOR, width=1)

            # Model Identity
            draw.text((85, y + 22), model["name"], font=font_label, fill=TEXT_WHITE)
            draw.text((85, y + 54), model["provider"], font=font_meta, fill=TEXT_MUTED)

            # Bar Geometry
            bar_x = 380
            bar_y = y + 26
            bar_h = 40
            
            # Target width based on TPS
            target_w = int((model["tps"] / float(max_tps)) * max_bar_width)
            current_w = max(10, int(target_w * progress))

            # Background Track
            draw.rounded_rectangle([(bar_x, bar_y), (bar_x + max_bar_width, bar_y + bar_h)], radius=8, fill=(15, 23, 42))

            # Filled Animated Bar
            draw.rounded_rectangle([(bar_x, bar_y), (bar_x + current_w, bar_y + bar_h)], radius=8, fill=model["color"])

            # Metric Counter Values (ticking up)
            current_tps = int(model["tps"] * progress)
            current_ttft = int(model["ttft_ms"] * progress)
            stat_text = f"{current_tps} tok/s  •  {current_ttft}ms TTFT"
            draw.text((bar_x + max_bar_width + 20, y + 34), stat_text, font=font_val, fill=TEXT_WHITE)

        # 4. Footer Call-to-Action Bar
        draw.rounded_rectangle([(60, 930), (1020, 1020)], radius=14, fill=(15, 23, 42), outline=(37, 99, 235), width=2)
        draw.text((95, 960), "📊 Live interactive leaderboards across 266+ models: neubench.netlify.app", font=font_footer, fill=(147, 197, 253))

        # Save individual frame
        frame_path = temp_frames_dir / f"frame_{frame_idx:04d}.png"
        img.save(frame_path, "PNG")

    print("[VisualAnimator] Compiling frames into MP4 video with FFmpeg...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(temp_frames_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_mp4)
    ]
    res = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Clean up temp frames directory
    shutil.rmtree(temp_frames_dir, ignore_errors=True)

    if res.returncode == 0 and output_mp4.exists():
        size_kb = output_mp4.stat().st_size / 1024.0
        print(f"[VisualAnimator] ✅ Animation rendered successfully: {output_mp4} ({size_kb:.1f} KB)")
        return output_mp4
    else:
        print(f"[VisualAnimator] ❌ FFmpeg error: {res.stderr.decode('utf-8', errors='ignore')}")
        return None

if __name__ == "__main__":
    out = BASE_DIR / "animated_benchmark_demo.mp4"
    render_benchmark_animation(out)
