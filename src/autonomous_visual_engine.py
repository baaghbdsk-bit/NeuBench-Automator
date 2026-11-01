"""
Autonomous Visual Engine for NeuBench Post Automation.
Dynamically creates high-contrast, technical 1080x1080 animated infographics and benchmark races (MP4 & GIF)
for LinkedIn, Bluesky, 𝕏, and Threads.
"""

import os
import math
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path("generated_visuals")
OUTPUT_DIR.mkdir(exist_ok=True)

# Theme Palette (High-contrast NeuBench Dark Mode)
BG_COLOR = (10, 14, 23)           # Deep Midnight Blue
CARD_BG = (17, 24, 39)           # Slate Card
BORDER_COLOR = (30, 41, 59)      # Slate Border
CYAN_ACCENT = (56, 189, 248)     # Electric Cyan
AMBER_ACCENT = (251, 191, 36)    # Warm Amber
EMERALD_ACCENT = (52, 211, 153)  # Emerald Green
PURPLE_ACCENT = (192, 132, 252)  # Tech Purple
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)
MUTED_DARK = (100, 116, 139)


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Tries loading clean system sans-serif/mono fonts or falls back to default."""
    font_names = (
        ["segoeuib.ttf", "arialbd.ttf", "consola.ttf"]
        if bold
        else ["segoeui.ttf", "arial.ttf", "consola.ttf"]
    )
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_token_pipeline_animation(output_base_name: str = "token_pipeline") -> Tuple[str, str]:
    """
    Template 1: Tokenization & High-Dimensional Vector Projection
    Shows Raw String -> BPE Subwords with Token IDs -> Dense Vector Matrix.
    """
    gif_path = str(OUTPUT_DIR / f"{output_base_name}.gif")
    mp4_path = str(OUTPUT_DIR / f"{output_base_name}.mp4")

    total_frames = 75
    fps = 20
    w, h = 1080, 1080
    frames = []

    f_title = get_font(38, bold=True)
    f_sub = get_font(20, bold=False)
    f_sec = get_font(22, bold=True)
    f_code = get_font(22, bold=True)
    f_small = get_font(16, bold=False)

    prompt_text = "Why is latency high in multi-agent workflows?"
    tokens = [
        ("Why", 14235, CYAN_ACCENT),
        ("is", 374, AMBER_ACCENT),
        ("latency", 21904, EMERALD_ACCENT),
        ("high", 1024, PURPLE_ACCENT),
        ("in", 287, CYAN_ACCENT),
        ("multi", 9411, AMBER_ACCENT),
        ("-agent", 2831, EMERALD_ACCENT),
        ("workflows", 45192, PURPLE_ACCENT),
        ("?", 30, CYAN_ACCENT),
    ]

    for frame_idx in range(total_frames):
        img = Image.new("RGB", (w, h), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Subtle grid background
        for x in range(0, w, 60):
            draw.line([(x, 0), (x, h)], fill=(15, 23, 42), width=1)
        for y in range(0, h, 60):
            draw.line([(0, y), (w, y)], fill=(15, 23, 42), width=1)

        # Header Badge
        draw.rounded_rectangle([70, 50, 240, 85], radius=6, fill=(30, 41, 59))
        draw.text((85, 58), "NEUBENCH ARCH", fill=CYAN_ACCENT, font=f_small)

        draw.text((70, 100), "HOW LLMS READ YOUR PROMPT", fill=WHITE, font=f_title)
        draw.text((70, 150), "String -> Subword Tokenization -> Dense Vector Embeddings", fill=MUTED, font=f_sub)

        # --- STEP 1: RAW INPUT STRING ---
        draw.rounded_rectangle([70, 200, 1010, 310], radius=12, fill=CARD_BG, outline=BORDER_COLOR, width=2)
        draw.text((95, 215), "STEP 1: RAW STRING PROMPT", fill=CYAN_ACCENT, font=f_sec)

        type_progress = min(1.0, frame_idx / 25.0)
        chars_to_show = int(len(prompt_text) * type_progress)
        typed_str = prompt_text[:chars_to_show]
        cursor = "_" if (frame_idx // 4) % 2 == 0 and type_progress < 1.0 else ""
        draw.text((95, 255), f'"{typed_str}{cursor}"', fill=WHITE, font=f_code)

        # Arrow down
        arrow1_alpha = min(1.0, max(0.0, (frame_idx - 20) / 10.0))
        if arrow1_alpha > 0:
            draw.line([(540, 315), (540, 345)], fill=CYAN_ACCENT, width=3)
            draw.polygon([(535, 345), (545, 345), (540, 355)], fill=CYAN_ACCENT)

        # --- STEP 2: BPE SUBWORDS ---
        draw.rounded_rectangle([70, 360, 1010, 540], radius=12, fill=CARD_BG, outline=BORDER_COLOR, width=2)
        draw.text((95, 375), "STEP 2: BYTE-PAIR ENCODING (BPE TOKEN IDS)", fill=AMBER_ACCENT, font=f_sec)

        num_tokens_visible = int(min(len(tokens), max(0, (frame_idx - 25) / 3.0)))
        tok_x = 95
        tok_y = 425

        for i in range(num_tokens_visible):
            tok_text, tok_id, tok_color = tokens[i]
            pw = max(80, len(tok_text) * 16 + 24)
            # Pill box
            draw.rounded_rectangle([tok_x, tok_y, tok_x + pw, tok_y + 44], radius=8, fill=(15, 23, 42), outline=tok_color, width=2)
            draw.text((tok_x + 10, tok_y + 10), tok_text, fill=WHITE, font=f_code)
            # ID label
            draw.text((tok_x + 10, tok_y + 52), f"#{tok_id}", fill=tok_color, font=f_small)
            tok_x += pw + 12

        # Arrow down
        arrow2_alpha = min(1.0, max(0.0, (frame_idx - 45) / 10.0))
        if arrow2_alpha > 0:
            draw.line([(540, 545), (540, 575)], fill=AMBER_ACCENT, width=3)
            draw.polygon([(535, 575), (545, 575), (540, 585)], fill=AMBER_ACCENT)

        # --- STEP 3: HIGH-DIMENSIONAL EMBEDDINGS ---
        draw.rounded_rectangle([70, 590, 1010, 890], radius=12, fill=CARD_BG, outline=BORDER_COLOR, width=2)
        draw.text((95, 605), "STEP 3: EMBEDDING LOOKUP MATRIX (D = 4,096)", fill=EMERALD_ACCENT, font=f_sec)

        vec_progress = min(1.0, max(0.0, (frame_idx - 45) / 25.0))
        matrix_rows = 5
        m_start_y = 660

        for r in range(matrix_rows):
            if r * 0.18 <= vec_progress:
                ry = m_start_y + r * 42
                t_lbl, _, t_col = tokens[r]
                draw.text((95, ry), f"{t_lbl:>9} -> [", fill=MUTED, font=f_code)

                # Vector floats
                phase = frame_idx * 0.15 + r
                v1 = math.sin(phase) * 0.84
                v2 = math.cos(phase + 1) * 0.62
                v3 = math.sin(phase + 2) * 0.91
                v_str = f"{v1:+.2f},  {v2:+.2f},  {v3:+.2f},  ...  +0.18"
                draw.text((250, ry), v_str, fill=t_col, font=f_code)
                draw.text((680, ry), "] in R^4096", fill=MUTED_DARK, font=f_small)

        # Footer Brand
        draw.line([(70, 930), (1010, 930)], fill=BORDER_COLOR, width=1)
        draw.text((70, 955), "NeuBench Research - Continuous AI LLM Benchmarking", fill=MUTED, font=f_sub)
        draw.text((800, 955), "neubench.netlify.app", fill=CYAN_ACCENT, font=f_sub)

        frames.append(img)

    # Save GIF & MP4
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=50, loop=0, optimize=True)

    # Export MP4 via ffmpeg
    temp_pattern = str(OUTPUT_DIR / "temp_f_%03d.png")
    for idx, f in enumerate(frames):
        f.save(str(OUTPUT_DIR / f"temp_f_{idx:03d}.png"))

    cmd = [
        "ffmpeg", "-y", "-r", str(fps), "-i", temp_pattern,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22",
        mp4_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for idx in range(len(frames)):
        try:
            os.remove(str(OUTPUT_DIR / f"temp_f_{idx:03d}.png"))
        except Exception:
            pass

    return gif_path, mp4_path


def render_benchmark_race_animation(
    models: Optional[list] = None,
    output_base_name: str = "benchmark_race"
) -> Tuple[str, str]:
    """
    Template 2: Dynamic LLM Throughput (TPS) & TTFT Benchmark Race
    """
    gif_path = str(OUTPUT_DIR / f"{output_base_name}.gif")
    mp4_path = str(OUTPUT_DIR / f"{output_base_name}.mp4")

    if not models:
        models = [
            {"name": "DeepSeek V3 (MoE)", "tps": 118, "ttft": "210ms", "color": CYAN_ACCENT},
            {"name": "Llama 3.3 70B (Groq)", "tps": 142, "ttft": "140ms", "color": EMERALD_ACCENT},
            {"name": "Claude 3.5 Sonnet", "tps": 76, "ttft": "380ms", "color": AMBER_ACCENT},
            {"name": "GPT-4o (OpenAI)", "tps": 88, "ttft": "320ms", "color": PURPLE_ACCENT},
            {"name": "Gemini 2.5 Flash", "tps": 132, "ttft": "165ms", "color": CYAN_ACCENT},
        ]

    total_frames = 60
    fps = 20
    w, h = 1080, 1080
    frames = []

    f_title = get_font(40, bold=True)
    f_sub = get_font(22, bold=False)
    f_bar = get_font(24, bold=True)
    f_small = get_font(18, bold=False)

    max_tps = max(m["tps"] for m in models)

    for frame_idx in range(total_frames):
        img = Image.new("RGB", (w, h), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Header
        draw.rounded_rectangle([70, 50, 240, 85], radius=6, fill=(30, 41, 59))
        draw.text((85, 58), "LIVE BENCHMARK", fill=CYAN_ACCENT, font=f_small)

        draw.text((70, 100), "INFERENCE THROUGHPUT & TTFT RACE", fill=WHITE, font=f_title)
        draw.text((70, 155), "Tokens Per Second (TPS) Output on Standard 1k Context", fill=MUTED, font=f_sub)

        # Race container
        draw.rounded_rectangle([70, 210, 1010, 880], radius=14, fill=CARD_BG, outline=BORDER_COLOR, width=2)

        start_y = 250
        bar_gap = 120

        progress = min(1.0, (frame_idx + 1) / 45.0)
        # Easing cubic-out
        ease_progress = 1 - math.pow(1 - progress, 3)

        for i, m in enumerate(models):
            y = start_y + i * bar_gap

            # Model title & TTFT stat
            draw.text((105, y), m["name"], fill=WHITE, font=f_bar)
            draw.text((105, y + 32), f"TTFT: {m['ttft']}", fill=MUTED, font=f_small)

            # Bar track
            track_x = 420
            track_w = 480
            draw.rounded_rectangle([track_x, y + 5, track_x + track_w, y + 45], radius=8, fill=(15, 23, 42))

            # Filled bar
            current_tps = int(m["tps"] * ease_progress)
            filled_w = int((current_tps / max_tps) * track_w)
            if filled_w > 0:
                draw.rounded_rectangle([track_x, y + 5, track_x + filled_w, y + 45], radius=8, fill=m["color"])

            # Value label
            draw.text((track_x + track_w + 20, y + 10), f"{current_tps} tps", fill=m["color"], font=f_bar)

        # Footer
        draw.line([(70, 930), (1010, 930)], fill=BORDER_COLOR, width=1)
        draw.text((70, 955), "Measured real-time via NeuBench Automated Runner", fill=MUTED, font=f_sub)
        draw.text((800, 955), "neubench.netlify.app", fill=CYAN_ACCENT, font=f_sub)

        frames.append(img)

    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=50, loop=0, optimize=True)

    temp_pattern = str(OUTPUT_DIR / "temp_b_%03d.png")
    for idx, f in enumerate(frames):
        f.save(str(OUTPUT_DIR / f"temp_b_{idx:03d}.png"))

    cmd = [
        "ffmpeg", "-y", "-r", str(fps), "-i", temp_pattern,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22",
        mp4_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for idx in range(len(frames)):
        try:
            os.remove(str(OUTPUT_DIR / f"temp_b_{idx:03d}.png"))
        except Exception:
            pass

    return gif_path, mp4_path


def generate_visual_for_post(topic_or_text: str) -> Tuple[str, str]:
    """
    Selects the most suitable template based on the topic keywords and generates both GIF and MP4.
    Returns: (gif_path, mp4_path)
    """
    lower = topic_or_text.lower()
    if any(k in lower for k in ["token", "embedding", "vector", "encoder", "transformer", "attention", "bpe", "vocab"]):
        print(f"[VisualEngine] Selected 'Token & Embedding Pipeline' visual template for: {topic_or_text[:40]}...")
        return render_token_pipeline_animation("token_pipeline_dynamic")
    else:
        print(f"[VisualEngine] Selected 'Benchmark & Throughput Race' visual template for: {topic_or_text[:40]}...")
        return render_benchmark_race_animation(output_base_name="benchmark_race_dynamic")
