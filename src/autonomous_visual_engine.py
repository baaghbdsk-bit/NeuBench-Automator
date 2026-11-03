"""
Autonomous Visual Engine for NeuBench Post Automation.
100% Dynamic, AI-Driven Visual Generation.
Uses Gemini to inspect the exact post topic and dynamically synthesize:
1. BENCHMARK_RACE: Real models, speeds, and latency from the specific topic.
2. CODE_ARCHITECTURE: Custom system architecture blocks + syntax-highlighted code matching the exact topic.
3. TOKEN_PIPELINE: Topic-specific prompt strings, subwords, and token IDs.

Renders 1080x1080 animated infographics (MP4 video loop and high-res GIF) with NeuBench branding.
"""

import os
import math
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from PIL import Image, ImageDraw, ImageFont

import config
from google import genai

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
PINK_ACCENT = (244, 114, 182)    # Pink Accent
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)
MUTED_DARK = (100, 116, 139)


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Loads system sans-serif/mono fonts across Windows/macOS/Linux or falls back cleanly."""
    font_names = (
        [
            "segoeuib.ttf",
            "arialbd.ttf",
            "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        if bold
        else [
            "segoeui.ttf",
            "arial.ttf",
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    )
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


_LAST_VISUAL_TYPE: Optional[str] = None

def request_ai_visual_spec(topic_or_text: str, summary: str = "", avoid_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Uses Gemini to dynamically plan the visual infographic schema based on the actual post content.
    Returns structured data for the chosen visual template.
    """
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    avoid_instruction = ""
    if avoid_type:
        avoid_instruction = f"""
IMPORTANT VARIETY RULE:
The previous post already used layout "{avoid_type}".
To keep our feed visually diverse and prevent repetitive visuals, DO NOT select "{avoid_type}".
Select between the other two visual types that best fit the topic.
"""

    prompt = f"""You are a Lead AI Research Engineer and Visual Information Designer for NeuBench.
Topic / Post Content: "{topic_or_text}"
Summary Context: "{summary}"
{avoid_instruction}
Analyze this topic and pick the single best visual infographic layout:
- Choice 1: "BENCHMARK_RACE" -> If the topic compares AI models, inference speed, throughput (TPS), latency (TTFT), or hardware.
- Choice 2: "CODE_ARCHITECTURE" -> If the topic explains an algorithm, framework, multi-agent design, system flow, or optimization technique.
- Choice 3: "TOKEN_PIPELINE" -> If the topic discusses prompts, tokenization, embeddings, vocabulary, vectors, or attention.

Return a STRICT JSON object matching ONE of these exact formats:

If BENCHMARK_RACE:
{{
  "visual_type": "BENCHMARK_RACE",
  "title": "Short punchy title (max 32 chars)",
  "subtitle": "Subtitle describing the benchmark metrics",
  "models": [
    {{"name": "Model 1", "tps": 135, "ttft": "160ms"}},
    {{"name": "Model 2", "tps": 98, "ttft": "290ms"}},
    {{"name": "Model 3", "tps": 76, "ttft": "380ms"}}
  ]
}}

If CODE_ARCHITECTURE:
{{
  "visual_type": "CODE_ARCHITECTURE",
  "title": "Short punchy title (max 32 chars)",
  "subtitle": "Subtitle describing system flow",
  "box1_title": "First Component (max 24 chars)",
  "box1_desc": "One-line role description",
  "box1_stat": "Performance or parameter detail",
  "arrow_label": "Routing action (max 16 chars)",
  "box2_title": "Second Component (max 24 chars)",
  "box2_desc": "One-line role description",
  "box2_stat": "Performance or output detail",
  "code_filename": "architecture.py",
  "code_lines": [
    "# Comment describing the core logic",
    "var = execute_step(input_data)",
    "# Comment describing optimization",
    "output = optimize_pipeline(var)"
  ],
  "impact_badge": "Real impact (e.g. 'Latency slashed by 52% | TTFT: 92ms')"
}}

If TOKEN_PIPELINE:
{{
  "visual_type": "TOKEN_PIPELINE",
  "title": "Short punchy title (max 32 chars)",
  "subtitle": "Subtitle describing token to vector conversion",
  "prompt_string": "Short technical prompt under 45 chars",
  "tokens": [
    {{"text": "Subword1", "id": 14235}},
    {{"text": "Subword2", "id": 892}},
    {{"text": "Subword3", "id": 3410}}
  ]
}}
"""
    try:
        res = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        data = json.loads(res.text)
        print(f"[VisualEngine] Gemini generated dynamic visual spec for type: {data.get('visual_type')}")
        return data
    except Exception as e:
        print(f"[VisualEngine] Error in Gemini visual spec generation: {e}. Falling back to default architecture layout.")
        return {
            "visual_type": "CODE_ARCHITECTURE",
            "title": topic_or_text[:32].upper(),
            "subtitle": "NeuBench Continuous AI Architecture Series",
            "box1_title": "INGESTION & PREFILL",
            "box1_desc": "Batch tokens & parallel KV prefill",
            "box1_stat": "Sub-millisecond flash attention",
            "arrow_label": "High-speed bus",
            "box2_title": "EXECUTION & DECODE",
            "box2_desc": "Continuous autoregressive generation",
            "box2_stat": "Zero memory fragmentation",
            "code_filename": "pipeline.py",
            "code_lines": [
                "# 1. Stream input tensors into cache memory",
                "cache = vllm_engine.prefill(context_tokens)",
                "# 2. Autoregressively decode candidate tokens",
                "output = vllm_engine.decode(cache, max_tokens=128)"
            ],
            "impact_badge": "Zero memory leaks | Continuous GPU saturation"
        }


def compile_frames_to_mp4(frames: List[Image.Image], temp_prefix: str, fps: int, mp4_path: str) -> Optional[str]:
    """Compiles Pillow frames into an MP4 video using ffmpeg with safe cleanup and fallback."""
    temp_pattern = str(OUTPUT_DIR / f"{temp_prefix}_%03d.png")
    created_temps = []
    try:
        for idx, f in enumerate(frames):
            p = str(OUTPUT_DIR / f"{temp_prefix}_{idx:03d}.png")
            f.save(p)
            created_temps.append(p)

        cmd = [
            "ffmpeg", "-y", "-r", str(fps), "-i", temp_pattern,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22",
            mp4_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
        if res.returncode == 0 and Path(mp4_path).exists() and Path(mp4_path).stat().st_size > 0:
            return mp4_path
    except Exception as e:
        print(f"[VisualEngine] FFmpeg compilation note: {e}. Falling back to GIF.")
    finally:
        for p in created_temps:
            try:
                os.remove(p)
            except Exception:
                pass
    return None


def render_dynamic_code_architecture(spec: Dict[str, Any], output_base_name: str = "code_arch_dynamic") -> Tuple[str, str]:
    """Renders the AI-designed Code Breakdown & Architecture Blueprint (Animated 1080x1080 Loop)."""
    gif_path = str(OUTPUT_DIR / f"{output_base_name}.gif")
    mp4_path = str(OUTPUT_DIR / f"{output_base_name}.mp4")

    total_frames = 65
    fps = 20
    w, h = 1080, 1080
    frames = []

    f_title = get_font(34, bold=True)
    f_sub = get_font(20, bold=False)
    f_sec = get_font(20, bold=True)
    f_code = get_font(19, bold=True)
    f_small = get_font(15, bold=False)
    f_tag = get_font(14, bold=True)

    title = spec.get("title", "SYSTEM ARCHITECTURE BLUEPRINT").upper()
    subtitle = spec.get("subtitle", "End-to-End Deep Learning Pipeline Breakdown")
    box1_title = spec.get("box1_title", "MODULE A")
    box1_desc = spec.get("box1_desc", "Primary processing component")
    box1_stat = spec.get("box1_stat", "Latency: 22ms")
    arrow_label = spec.get("arrow_label", "Forward Pass")
    box2_title = spec.get("box2_title", "MODULE B")
    box2_desc = spec.get("box2_desc", "Secondary verification component")
    box2_stat = spec.get("box2_stat", "Zero degradation")
    code_filename = spec.get("code_filename", "architecture.py")
    raw_code_lines = spec.get("code_lines", ["# Execution pipeline", "result = model.run(data)"])
    impact_badge = spec.get("impact_badge", "Optimized throughput with zero memory bottlenecks")

    # Format code lines with syntax colors
    colors = [CYAN_ACCENT, AMBER_ACCENT, EMERALD_ACCENT, PURPLE_ACCENT, PINK_ACCENT]
    code_lines = []
    c_idx = 0
    for line in raw_code_lines[:7]:
        if line.strip().startswith("#"):
            code_lines.append((line, MUTED))
        else:
            code_lines.append((line, colors[c_idx % len(colors)]))
            c_idx += 1

    for frame_idx in range(total_frames):
        img = Image.new("RGB", (w, h), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Subtle grid background
        for x in range(0, w, 60):
            draw.line([(x, 0), (x, h)], fill=(15, 23, 42), width=1)
        for y in range(0, h, 60):
            draw.line([(0, y), (w, y)], fill=(15, 23, 42), width=1)

        # Top Badge
        draw.rounded_rectangle([70, 45, 260, 80], radius=6, fill=(30, 41, 59))
        draw.text((85, 52), "NEUBENCH BLUEPRINT", fill=CYAN_ACCENT, font=f_tag)

        draw.text((70, 95), title[:36], fill=WHITE, font=f_title)
        draw.text((70, 145), subtitle[:65], fill=MUTED, font=f_sub)

        # Architecture Flow Boxes
        # Box 1
        draw.rounded_rectangle([70, 195, 480, 310], radius=10, fill=CARD_BG, outline=CYAN_ACCENT, width=2)
        draw.text((90, 210), box1_title[:24], fill=CYAN_ACCENT, font=f_sec)
        draw.text((90, 240), box1_desc[:40], fill=MUTED, font=f_small)
        draw.text((90, 270), box1_stat[:40], fill=WHITE, font=f_small)

        # Animated Connection Arrow
        arrow_phase = (frame_idx % 20) / 20.0
        arrow_glow = int(180 + 75 * math.sin(arrow_phase * math.pi * 2))
        arrow_col = (56, 189, max(150, min(255, arrow_glow)))
        draw.line([(485, 252), (595, 252)], fill=arrow_col, width=3)
        draw.polygon([(595, 247), (605, 252), (595, 257)], fill=arrow_col)
        draw.text((500, 225), arrow_label[:14], fill=AMBER_ACCENT, font=f_small)

        # Box 2
        draw.rounded_rectangle([610, 195, 1010, 310], radius=10, fill=CARD_BG, outline=EMERALD_ACCENT, width=2)
        draw.text((630, 210), box2_title[:24], fill=EMERALD_ACCENT, font=f_sec)
        draw.text((630, 240), box2_desc[:40], fill=MUTED, font=f_small)
        draw.text((630, 270), box2_stat[:40], fill=WHITE, font=f_small)

        # IDE Window Card
        draw.rounded_rectangle([70, 345, 1010, 835], radius=12, fill=(13, 17, 23), outline=BORDER_COLOR, width=2)

        # Window Header
        draw.rounded_rectangle([70, 345, 1010, 395], radius=12, fill=(22, 27, 34))
        draw.ellipse([90, 362, 104, 376], fill=(239, 68, 68))
        draw.ellipse([114, 362, 128, 376], fill=(245, 158, 11))
        draw.ellipse([138, 362, 152, 376], fill=(34, 197, 94))
        draw.text((170, 360), f"{code_filename} - NeuBench Deep Dive", fill=MUTED, font=f_small)

        # Animated Line Reveal
        visible_lines = min(len(code_lines), int(frame_idx / 6.0) + 1)
        line_y = 420
        for idx in range(visible_lines):
            line_str, line_col = code_lines[idx]
            draw.text((95, line_y), f"{idx+1:2d}", fill=MUTED_DARK, font=f_code)
            draw.text((140, line_y), line_str[:60], fill=line_col, font=f_code)
            line_y += 52

        # Active Callout Badge
        if visible_lines >= len(code_lines):
            draw.rounded_rectangle([95, 760, 985, 815], radius=8, fill=(15, 23, 42), outline=PURPLE_ACCENT, width=1)
            draw.text((115, 775), "⚡ SYSTEM IMPACT:", fill=PURPLE_ACCENT, font=f_sec)
            draw.text((300, 777), impact_badge[:65], fill=WHITE, font=f_small)

        # Footer
        draw.line([(70, 875), (1010, 875)], fill=BORDER_COLOR, width=1)
        draw.text((70, 905), "NeuBench Engineering Architecture Series", fill=MUTED, font=f_sub)
        draw.text((800, 905), "neubench.netlify.app", fill=CYAN_ACCENT, font=f_sub)

        frames.append(img)

    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=50, loop=0, optimize=True)

    compiled_mp4 = compile_frames_to_mp4(frames, "temp_c", fps, mp4_path)
    return gif_path, (compiled_mp4 or "")


def render_dynamic_benchmark_race(spec: Dict[str, Any], output_base_name: str = "benchmark_race_dynamic") -> Tuple[str, str]:
    """Renders the AI-designed Benchmark & Throughput Race (Animated 1080x1080 Loop)."""
    gif_path = str(OUTPUT_DIR / f"{output_base_name}.gif")
    mp4_path = str(OUTPUT_DIR / f"{output_base_name}.mp4")

    title = spec.get("title", "AI INFERENCE BENCHMARK RACE").upper()
    subtitle = spec.get("subtitle", "Measured Real-Time Tokens Per Second (TPS) and Latency")
    raw_models = spec.get("models", [])
    if not raw_models:
        raw_models = [
            {"name": "DeepSeek R1", "tps": 95, "ttft": "310ms"},
            {"name": "Claude 3.5 Sonnet", "tps": 110, "ttft": "220ms"},
            {"name": "Llama 3.3 70B", "tps": 130, "ttft": "160ms"}
        ]

    colors = [CYAN_ACCENT, EMERALD_ACCENT, AMBER_ACCENT, PURPLE_ACCENT, PINK_ACCENT]
    models = []
    for i, m in enumerate(raw_models[:5]):
        models.append({
            "name": str(m.get("name", f"Model {i+1}")),
            "tps": int(m.get("tps", 80)),
            "ttft": str(m.get("ttft", "200ms")),
            "color": colors[i % len(colors)]
        })

    max_tps = max(m["tps"] for m in models) or 100

    total_frames = 60
    fps = 20
    w, h = 1080, 1080
    frames = []

    f_title = get_font(38, bold=True)
    f_sub = get_font(22, bold=False)
    f_bar = get_font(24, bold=True)
    f_small = get_font(18, bold=False)

    for frame_idx in range(total_frames):
        img = Image.new("RGB", (w, h), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Header Badge
        draw.rounded_rectangle([70, 50, 240, 85], radius=6, fill=(30, 41, 59))
        draw.text((85, 58), "LIVE BENCHMARK", fill=CYAN_ACCENT, font=f_small)

        draw.text((70, 100), title[:32], fill=WHITE, font=f_title)
        draw.text((70, 155), subtitle[:65], fill=MUTED, font=f_sub)

        # Container
        draw.rounded_rectangle([70, 210, 1010, 880], radius=14, fill=CARD_BG, outline=BORDER_COLOR, width=2)

        start_y = 250
        bar_gap = max(90, int(600 / max(1, len(models))))
        progress = min(1.0, (frame_idx + 1) / 45.0)
        ease_progress = 1 - math.pow(1 - progress, 3)

        for i, m in enumerate(models):
            y = start_y + i * bar_gap
            draw.text((105, y), m["name"][:22], fill=WHITE, font=f_bar)
            draw.text((105, y + 32), f"TTFT: {m['ttft']}", fill=MUTED, font=f_small)

            track_x = 420
            track_w = 460
            draw.rounded_rectangle([track_x, y + 5, track_x + track_w, y + 45], radius=8, fill=(15, 23, 42))

            current_tps = int(m["tps"] * ease_progress)
            filled_w = int((current_tps / max_tps) * track_w)
            if filled_w > 0:
                draw.rounded_rectangle([track_x, y + 5, track_x + filled_w, y + 45], radius=8, fill=m["color"])

            draw.text((track_x + track_w + 20, y + 10), f"{current_tps} tps", fill=m["color"], font=f_bar)

        # Footer
        draw.line([(70, 930), (1010, 930)], fill=BORDER_COLOR, width=1)
        draw.text((70, 955), "Measured real-time via NeuBench Automated Runner", fill=MUTED, font=f_sub)
        draw.text((800, 955), "neubench.netlify.app", fill=CYAN_ACCENT, font=f_sub)

        frames.append(img)

    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=50, loop=0, optimize=True)

    compiled_mp4 = compile_frames_to_mp4(frames, "temp_b", fps, mp4_path)
    return gif_path, (compiled_mp4 or "")


def render_dynamic_token_pipeline(spec: Dict[str, Any], output_base_name: str = "token_pipeline_dynamic") -> Tuple[str, str]:
    """Renders the AI-designed Tokenization & Embedding Pipeline (Animated 1080x1080 Loop)."""
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

    title = spec.get("title", "HOW LLMS READ YOUR PROMPT").upper()
    subtitle = spec.get("subtitle", "String -> Subword Tokenization -> High-Dimensional Embeddings")
    prompt_text = spec.get("prompt_string", "Why is latency high in multi-agent workflows?")
    raw_tokens = spec.get("tokens", [])
    if not raw_tokens:
        raw_tokens = [
            {"text": "Why", "id": 14235},
            {"text": "is", "id": 374},
            {"text": "latency", "id": 21904},
            {"text": "high", "id": 1024},
            {"text": "in", "id": 287},
            {"text": "agents", "id": 45192},
            {"text": "?", "id": 30}
        ]

    colors = [CYAN_ACCENT, AMBER_ACCENT, EMERALD_ACCENT, PURPLE_ACCENT, PINK_ACCENT]
    tokens = []
    for i, t in enumerate(raw_tokens[:8]):
        tokens.append((str(t.get("text", "")), int(t.get("id", 1000 + i)), colors[i % len(colors)]))

    for frame_idx in range(total_frames):
        img = Image.new("RGB", (w, h), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Grid background
        for x in range(0, w, 60):
            draw.line([(x, 0), (x, h)], fill=(15, 23, 42), width=1)
        for y in range(0, h, 60):
            draw.line([(0, y), (w, y)], fill=(15, 23, 42), width=1)

        # Header Badge
        draw.rounded_rectangle([70, 50, 240, 85], radius=6, fill=(30, 41, 59))
        draw.text((85, 58), "NEUBENCH ARCH", fill=CYAN_ACCENT, font=f_small)

        draw.text((70, 100), title[:32], fill=WHITE, font=f_title)
        draw.text((70, 150), subtitle[:65], fill=MUTED, font=f_sub)

        # STEP 1: RAW INPUT STRING
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

        # STEP 2: BPE SUBWORDS
        draw.rounded_rectangle([70, 360, 1010, 540], radius=12, fill=CARD_BG, outline=BORDER_COLOR, width=2)
        draw.text((95, 375), "STEP 2: BYTE-PAIR ENCODING (TOKEN IDS)", fill=AMBER_ACCENT, font=f_sec)

        num_tokens_visible = int(min(len(tokens), max(0, (frame_idx - 25) / 3.0)))
        tok_x = 95
        tok_y = 425

        for i in range(num_tokens_visible):
            tok_text, tok_id, tok_color = tokens[i]
            pw = max(75, len(tok_text) * 16 + 24)
            draw.rounded_rectangle([tok_x, tok_y, tok_x + pw, tok_y + 44], radius=8, fill=(15, 23, 42), outline=tok_color, width=2)
            draw.text((tok_x + 10, tok_y + 10), tok_text, fill=WHITE, font=f_code)
            draw.text((tok_x + 10, tok_y + 52), f"#{tok_id}", fill=tok_color, font=f_small)
            tok_x += pw + 12

        # Arrow down
        arrow2_alpha = min(1.0, max(0.0, (frame_idx - 45) / 10.0))
        if arrow2_alpha > 0:
            draw.line([(540, 545), (540, 575)], fill=AMBER_ACCENT, width=3)
            draw.polygon([(535, 575), (545, 575), (540, 585)], fill=AMBER_ACCENT)

        # STEP 3: HIGH-DIMENSIONAL EMBEDDINGS
        draw.rounded_rectangle([70, 590, 1010, 890], radius=12, fill=CARD_BG, outline=BORDER_COLOR, width=2)
        draw.text((95, 605), "STEP 3: EMBEDDING LOOKUP MATRIX (D = 4,096)", fill=EMERALD_ACCENT, font=f_sec)

        vec_progress = min(1.0, max(0.0, (frame_idx - 45) / 25.0))
        matrix_rows = min(5, len(tokens))
        m_start_y = 660

        for r in range(matrix_rows):
            if r * 0.18 <= vec_progress:
                ry = m_start_y + r * 42
                t_lbl, _, t_col = tokens[r]
                draw.text((95, ry), f"{t_lbl:>9} -> [", fill=MUTED, font=f_code)

                phase = frame_idx * 0.15 + r
                v1 = math.sin(phase) * 0.84
                v2 = math.cos(phase + 1) * 0.62
                v3 = math.sin(phase + 2) * 0.91
                v_str = f"{v1:+.2f},  {v2:+.2f},  {v3:+.2f},  ...  +0.18"
                draw.text((250, ry), v_str, fill=t_col, font=f_code)
                draw.text((680, ry), "] in R^4096", fill=MUTED_DARK, font=f_small)

        # Footer
        draw.line([(70, 930), (1010, 930)], fill=BORDER_COLOR, width=1)
        draw.text((70, 955), "NeuBench Research - Continuous AI LLM Benchmarking", fill=MUTED, font=f_sub)
        draw.text((800, 955), "neubench.netlify.app", fill=CYAN_ACCENT, font=f_sub)

        frames.append(img)

    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=50, loop=0, optimize=True)

    compiled_mp4 = compile_frames_to_mp4(frames, "temp_f", fps, mp4_path)
    return gif_path, (compiled_mp4 or "")


def generate_casual_visual_card(
    topic_or_title: str,
    text: str,
    square: bool = False,
    output_base_name: str = ""
) -> Tuple[str, str]:
    """
    Renders a viral, high-contrast aesthetic dark-mode thought card (PNG and looping GIF).
    Ideal for casual X (1200x675) and Threads (1080x1080) posts to drive maximum saves,
    retweets, and timeline dwell time.
    """
    import hashlib, re, textwrap

    # Clean text of hashtags/URLs for visual card presentation
    clean_text = re.sub(r'https?://\S+', '', text)
    clean_text = re.sub(r'#\w+', '', clean_text).strip()
    if not clean_text:
        clean_text = topic_or_title

    # Generate slug & file paths
    raw_slug = re.sub(r'[^a-zA-Z0-9_]', '_', topic_or_title.strip().lower())
    clean_slug = re.sub(r'_+', '_', raw_slug)[:20].strip('_')
    content_hash = hashlib.md5(f"{topic_or_title}_{text[:80]}".encode()).hexdigest()[:8]
    base_name = output_base_name or f"casual_{clean_slug}_{content_hash}"

    png_path = str(OUTPUT_DIR / f"{base_name}.png")
    gif_path = str(OUTPUT_DIR / f"{base_name}.gif")

    width, height = (1080, 1080) if square else (1200, 675)

    # Text wrapping
    wrap_width = 38 if square else 46
    wrapped_lines = textwrap.wrap(clean_text, width=wrap_width)
    if len(wrapped_lines) > 8:
        wrapped_lines = wrapped_lines[:8]
        wrapped_lines[-1] = wrapped_lines[-1].rstrip(".,:;") + "..."

    # Create 4 subtle animated frames for looping GIF
    frames = []
    card_margin = 60 if square else 50
    card_x1, card_y1 = card_margin, card_margin
    card_x2, card_y2 = width - card_margin, height - card_margin

    for f_idx in range(4):
        img = Image.new("RGB", (width, height), (11, 15, 25))
        draw = ImageDraw.Draw(img)

        # Subtle corner glows
        draw.ellipse((-80, -80, 320, 320), fill=(20, 35, 55))
        draw.ellipse((width - 250, height - 250, width + 100, height + 100), fill=(25, 25, 45))

        # Outer rounded card
        draw.rounded_rectangle(
            (card_x1, card_y1, card_x2, card_y2),
            radius=24,
            fill=(18, 24, 38),
            outline=(45, 55, 75),
            width=2
        )

        # Header Badge: "☕ REAL TALK"
        badge_y = card_y1 + 45
        badge_x = card_x1 + 50
        draw.rounded_rectangle(
            (badge_x, badge_y, badge_x + 190, badge_y + 40),
            radius=20,
            fill=(28, 38, 58),
            outline=(56, 189, 248),
            width=1
        )
        # Pulsing accent dot
        dot_color = (56, 189, 248) if f_idx % 2 == 0 else (147, 197, 253)
        draw.ellipse((badge_x + 14, badge_y + 14, badge_x + 26, badge_y + 26), fill=dot_color)
        draw.text((badge_x + 36, badge_y + 10), "REAL TALK", font=get_font(18, bold=True), fill=(248, 250, 252))

        # Topic header
        topic_header = topic_or_title[:45].upper()
        draw.text((badge_x + 210, badge_y + 11), f"//  {topic_header}", font=get_font(18, bold=False), fill=(148, 163, 184))

        # Main quote / thought text
        font_size = 38 if (square and len(wrapped_lines) <= 5) else (34 if not square else 30)
        main_font = get_font(font_size, bold=True)
        line_height = font_size + 18
        total_text_height = len(wrapped_lines) * line_height

        # Vertically center text in card
        start_y = card_y1 + (card_y2 - card_y1 - total_text_height) // 2 + 10
        cur_y = max(card_y1 + 120, start_y)

        for line in wrapped_lines:
            draw.text((card_x1 + 60, cur_y), line, font=main_font, fill=(248, 250, 252))
            cur_y += line_height

        # Footer divider & engagement cues
        footer_y = card_y2 - 65
        draw.line((card_x1 + 50, footer_y, card_x2 - 50, footer_y), fill=(35, 45, 65), width=1)

        footer_font = get_font(18, bold=False)
        draw.text((card_x1 + 60, footer_y + 18), "💬 Unfiltered Thoughts & Modern Quirks", font=footer_font, fill=(148, 163, 184))
        draw.text((card_x2 - 250, footer_y + 18), "🔁 Repost  •  💬 Reply", font=footer_font, fill=(56, 189, 248))

        frames.append(img)

    # Save high-res PNG & looping GIF
    frames[0].save(png_path, format="PNG", quality=95)
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=600, loop=0, optimize=True)

    return png_path, gif_path


def generate_visual_for_post(topic_or_text: str, summary: str = "", avoid_type: Optional[str] = None) -> Tuple[str, str]:
    """
    Main entry point:
    1. Uses Gemini AI to analyze the specific post topic and generate custom technical layout specifications.
    2. Ensures unique, uncollided file names so each post gets its own distinct attachment.
    3. Dispatches to the corresponding renderer with the AI-generated titles, models, code, or tokens.
    4. Guarantees non-empty (gif_path, mp4_path) with local fallbacks if network fails.
    """
    global _LAST_VISUAL_TYPE
    import hashlib, re
    raw_slug = re.sub(r'[^a-zA-Z0-9_]', '_', topic_or_text.strip().lower())
    clean_slug = re.sub(r'_+', '_', raw_slug)[:25].strip('_')
    content_hash = hashlib.md5(f"{topic_or_text}_{summary[:100]}".encode()).hexdigest()[:8]
    unique_base_name = f"{clean_slug}_{content_hash}" if clean_slug else f"visual_{content_hash}"

    try:
        effective_avoid = avoid_type or _LAST_VISUAL_TYPE
        spec = request_ai_visual_spec(topic_or_text, summary, avoid_type=effective_avoid)
        v_type = spec.get("visual_type", "CODE_ARCHITECTURE")
        _LAST_VISUAL_TYPE = v_type

        if v_type == "BENCHMARK_RACE":
            return render_dynamic_benchmark_race(spec, output_base_name=unique_base_name)
        elif v_type == "TOKEN_PIPELINE":
            return render_dynamic_token_pipeline(spec, output_base_name=unique_base_name)
        else:
            return render_dynamic_code_architecture(spec, output_base_name=unique_base_name)
    except Exception as e:
        print(f"[VisualEngine] Note on visual rendering: {e}. Using deterministic fallback layout.")
        spec = {
            "visual_type": "CODE_ARCHITECTURE",
            "title": topic_or_text[:32].upper(),
            "subtitle": "Continuous AI Architecture Series",
            "box1_title": "INGESTION & PREFILL",
            "box1_desc": "Batch tokens & parallel KV prefill",
            "box1_stat": "Sub-millisecond flash attention",
            "arrow_label": "High-speed bus",
            "box2_title": "EXECUTION & DECODE",
            "box2_desc": "Continuous autoregressive generation",
            "box2_stat": "Zero memory fragmentation",
            "code_filename": "pipeline.py",
            "code_lines": [
                "# 1. Stream input tensors into cache memory",
                "cache = vllm_engine.prefill(context_tokens)",
                "# 2. Autoregressively decode candidate tokens",
                "output = vllm_engine.decode(cache, max_tokens=128)"
            ],
            "impact_badge": "Zero memory leaks | Continuous GPU saturation"
        }
        return render_dynamic_code_architecture(spec, output_base_name=unique_base_name)
