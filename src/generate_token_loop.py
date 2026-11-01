"""
NeuBench Looping GIF Generator: "How LLMs Convert Your Prompt into Tokens & Vectors".
Renders an animated 1080x1080 infographic loop showing:
1. Raw User Prompt: "Why is latency high in agents?"
2. Byte-Pair Encoding Tokenization: ["Why", " is", " latency", " high", " in", " agents", "?"]
3. Embedding Projection & Vector Tensor: [0.84, -0.12, 0.49, ...]
4. Multi-Head Attention & Transformer Compute.
"""
import os
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent

BG_COLOR = (10, 14, 23)        # Deep Midnight
CARD_BG = (17, 24, 39)         # Dark Container
BORDER_COLOR = (30, 41, 59)    # Border Slate
TEXT_WHITE = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)
ACCENT_CYAN = (56, 189, 248)
ACCENT_GREEN = (34, 197, 94)
ACCENT_PURPLE = (168, 85, 247)
ACCENT_AMBER = (251, 191, 36)

TOKENS = [
    {"text": "Why", "id": 13920, "color": (59, 130, 246)},
    {"text": " is", "id": 374, "color": (16, 185, 129)},
    {"text": " latency", "id": 31402, "color": (245, 158, 11)},
    {"text": " high", "id": 1344, "color": (236, 72, 153)},
    {"text": " in", "id": 304, "color": (139, 92, 246)},
    {"text": " agents", "id": 15421, "color": (14, 165, 233)},
    {"text": "?", "id": 30, "color": (239, 68, 68)},
]

def get_font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahomabd.ttf" if bold else "C:/Windows/Fonts/tahoma.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def render_llm_tokenization_loop(
    output_gif: Path,
    output_mp4: Path,
    fps: int = 20,
    duration_sec: float = 4.0
):
    output_gif = Path(output_gif)
    output_mp4 = Path(output_mp4)
    temp_dir = output_gif.parent / "_temp_token_frames"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    width, height = 1080, 1080
    total_frames = int(fps * duration_sec)

    f_badge = get_font(22, bold=True)
    f_title = get_font(38, bold=True)
    f_sub = get_font(21, bold=False)
    f_sec = get_font(26, bold=True)
    f_mono = get_font(24, bold=True)
    f_small = get_font(18, bold=False)
    f_foot = get_font(22, bold=True)

    for idx in range(total_frames):
        # Progress 0.0 to 1.0
        t = idx / float(total_frames)

        img = Image.new("RGB", (width, height), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Background Subtle Grid
        for x in range(0, width, 60):
            draw.line([(x, 0), (x, height)], fill=(16, 22, 34), width=1)
        for y in range(0, height, 60):
            draw.line([(0, y), (width, y)], fill=(16, 22, 34), width=1)

        # 1. Header Box
        draw.rounded_rectangle([(60, 50), (1020, 205)], radius=16, fill=CARD_BG, outline=BORDER_COLOR, width=2)
        # Badge
        draw.rounded_rectangle([(90, 72), (320, 110)], radius=8, fill=(30, 41, 59), outline=(51, 65, 85), width=1)
        draw.text((105, 78), "🧠 LLM ARCHITECTURE", font=f_badge, fill=ACCENT_CYAN)
        draw.ellipse([(298, 86), (308, 96)], fill=ACCENT_GREEN)

        draw.text((90, 122), "How LLMs Convert Your Prompt into Vectors", font=f_title, fill=TEXT_WHITE)
        draw.text((90, 170), "From Human Text → Subword Tokens → High-Dimensional Vectors", font=f_sub, fill=TEXT_MUTED)

        # 2. Step 1: Raw Prompt String (Typing effect in phase 1)
        draw.rounded_rectangle([(60, 235), (1020, 365)], radius=14, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((85, 250), "STEP 1: Raw String Input (UTF-8)", font=f_sec, fill=ACCENT_CYAN)

        full_prompt = '"Why is latency high in agents?"'
        # Typewriter effect from t=0.0 to t=0.3
        type_len = min(len(full_prompt), int(len(full_prompt) * min(1.0, t / 0.3)))
        typed_str = full_prompt[:type_len]
        draw.rounded_rectangle([(85, 290), (995, 345)], radius=8, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
        cursor = "_" if (idx % 6 < 3) else ""
        draw.text((105, 303), typed_str + cursor, font=f_mono, fill=TEXT_WHITE)

        # 3. Step 2: Byte-Pair Encoding (BPE Tokenization)
        draw.rounded_rectangle([(60, 395), (1020, 580)], radius=14, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((85, 410), "STEP 2: Byte-Pair Encoding (BPE) Subword Tokens", font=f_sec, fill=ACCENT_AMBER)

        # Animate tokens appearing between t=0.25 and t=0.65
        tok_start_x = 85
        tok_y = 455
        for i, tok in enumerate(TOKENS):
            token_threshold = 0.25 + (i / len(TOKENS)) * 0.40
            if t >= token_threshold:
                box_w = 115
                box_h = 95
                bx = tok_start_x + i * (box_w + 16)
                
                # Glowing card
                draw.rounded_rectangle([(bx, tok_y), (bx + box_w, tok_y + box_h)], radius=10, fill=(15, 23, 42), outline=tok["color"], width=2)
                # Token string
                draw.text((bx + 14, tok_y + 14), tok["text"], font=f_mono, fill=tok["color"])
                # Token ID
                draw.text((bx + 14, tok_y + 46), f"ID:{tok['id']}", font=f_small, fill=TEXT_MUTED)
                # Dimension tag
                draw.text((bx + 14, tok_y + 68), "dim: 4096", font=f_small, fill=(71, 85, 105))

        # 4. Step 3: Embedding Projection (Vector Weights)
        draw.rounded_rectangle([(60, 610), (1020, 890)], radius=14, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((85, 625), "STEP 3: Vector Embedding Table (4,096 Hidden Dimensions)", font=f_sec, fill=ACCENT_PURPLE)

        # Animated vector bar visual (active when t >= 0.5)
        vec_y = 675
        vec_progress = min(1.0, max(0.0, (t - 0.5) / 0.4))
        
        # Display a 2D matrix projection
        matrix_rows = [
            ("Token 'latency'", "[ +0.8412, -0.1944, +0.6219, ... +0.0381 ]", (245, 158, 11)),
            ("Token 'agents'",  "[ +0.7915, +0.3328, -0.4182, ... -0.1904 ]", (14, 165, 233)),
            ("Positional Cos", "[ +0.9881, +0.0412, +0.1192, ... +0.5512 ]", (168, 85, 247)),
        ]

        for r_idx, (lbl, vec_str, color) in enumerate(matrix_rows):
            ry = vec_y + r_idx * 65
            draw.text((85, ry + 12), lbl, font=f_mono, fill=TEXT_MUTED)
            # Animated vector box
            max_vw = 640
            current_vw = int(max_vw * vec_progress)
            draw.rounded_rectangle([(270, ry), (270 + max_vw, ry + 48)], radius=8, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
            if current_vw > 10:
                draw.rounded_rectangle([(270, ry), (270 + current_vw, ry + 48)], radius=8, fill=(30, 41, 59), outline=color, width=1)
                draw.text((285, ry + 12), vec_str, font=f_mono, fill=color)

        # 5. Footer CTA Bar
        draw.rounded_rectangle([(60, 930), (1020, 1020)], radius=14, fill=(15, 23, 42), outline=(37, 99, 235), width=2)
        draw.text((85, 960), "⚡ Benchmarking 266+ LLM embeddings & latency: neubench.netlify.app", font=f_foot, fill=(147, 197, 253))

        frame_path = temp_dir / f"frame_{idx:04d}.png"
        img.save(frame_path, "PNG")

    print(f"[LoopingGifGenerator] Compiled {total_frames} frames. Creating high-res GIF & MP4...")

    # 1. High-Quality Looping GIF via FFmpeg palettegen
    palette_path = temp_dir / "palette.png"
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(temp_dir / "frame_%04d.png"),
        "-vf", "palettegen=max_colors=128:stats_mode=diff",
        str(palette_path)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(temp_dir / "frame_%04d.png"),
        "-i", str(palette_path),
        "-lavfi", "paletteuse=dither=bayer:bayer_scale=3",
        "-loop", "0",
        str(output_gif)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 2. FastStart MP4 Video Loop (for native video uploads)
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(temp_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_mp4)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Clean frames
    shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"[LoopingGifGenerator] Completed! GIF: {output_gif.stat().st_size // 1024} KB, MP4: {output_mp4.stat().st_size // 1024} KB")
    return output_gif, output_mp4

if __name__ == "__main__":
    gif_file = BASE_DIR / "how_llms_convert_prompt.gif"
    mp4_file = BASE_DIR / "how_llms_convert_prompt.mp4"
    render_llm_tokenization_loop(gif_file, mp4_file)
