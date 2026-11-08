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
        print(f"[VisualEngine] Error in Gemini visual spec generation: {e}. Building deterministic topic-derived layout.")
        import re
        parts = [p.strip() for p in re.split(r' vs | and | to | in | for | - ', topic_or_text, flags=re.I) if p.strip()]
        b1_name = parts[0][:22].upper() if parts else "INPUT DISPATCH"
        b2_name = parts[1][:22].upper() if len(parts) > 1 else "PIPELINE SINK"
        file_slug = re.sub(r'[^a-zA-Z0-9_]', '_', topic_or_text.lower())[:16].strip('_') or "pipeline"
        clean_summary = summary.strip() if summary else f"{topic_or_text.strip()} Architecture"
        return {
            "visual_type": "CODE_ARCHITECTURE",
            "title": topic_or_text[:32].strip().upper(),
            "subtitle": clean_summary[:60],
            "box1_title": b1_name,
            "box1_desc": f"Process {b1_name.lower()} stage",
            "box1_stat": "Deterministic throughput",
            "arrow_label": "High-Speed Bus",
            "box2_title": b2_name,
            "box2_desc": f"Execute {b2_name.lower()} stage",
            "box2_stat": "Zero fragmentation",
            "code_filename": f"{file_slug}.py",
            "code_lines": [
                f"# Pipeline execution for {topic_or_text[:28]}",
                f"stage1 = dispatch_{b1_name.lower().replace(' ', '_')[:12]}(data)",
                f"# Optimization & execution",
                f"result = execute_{b2_name.lower().replace(' ', '_')[:12]}(stage1)",
            ],
            "impact_badge": f"⚡ SYSTEM IMPACT: Optimized {topic_or_text[:24]} throughput"
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
    """Renders the AI-designed Code Breakdown & Architecture Blueprint (Animated 1080x1080 Loop) using Manim."""
    from src.manim_renderer import render_scene
    return render_scene("code_arch_scene", "CodeArchitecture", output_base_name, spec=spec)


def render_dynamic_benchmark_race(spec: Dict[str, Any], output_base_name: str = "benchmark_race_dynamic") -> Tuple[str, str]:
    """Renders the AI-designed Benchmark & Throughput Race (Animated 1080x1080 Loop) using Manim."""
    from src.manim_renderer import render_scene
    return render_scene("benchmark_race_scene", "BenchmarkRace", output_base_name, spec=spec)


def render_dynamic_token_pipeline(spec: Dict[str, Any], output_base_name: str = "token_pipeline_dynamic") -> Tuple[str, str]:
    """Renders the AI-designed Tokenization & Embedding Pipeline (Animated 1080x1080 Loop) using Manim."""
    from src.manim_renderer import render_scene
    return render_scene("token_pipeline_scene", "TokenPipeline", output_base_name, spec=spec)


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
        print(f"[VisualEngine] Note on visual rendering: {e}. Suppressing attachment to prevent repeating off-topic visuals.")
        return ("", "")


def render_dynamic_concept_comparison(concept: Dict[str, Any], output_base_name: str = "concept_comp") -> Tuple[str, str]:
    """
    Renders an animated 1080x1080 looping GIF comparing two software/AI concepts side-by-side.
    High-contrast dark mode aesthetic with pulsating glows, scorecard metrics, and golden rules.
    """
    gif_path = str(OUTPUT_DIR / f"{output_base_name}.gif")
    mp4_path = str(OUTPUT_DIR / f"{output_base_name}.mp4")

    total_frames = 24
    fps = 16
    w, h = 1080, 1080
    frames = []

    f_title = get_font(34, bold=True)
    f_sub = get_font(19, bold=False)
    f_sec = get_font(21, bold=True)
    f_bold = get_font(18, bold=True)
    f_small = get_font(15, bold=False)
    f_tag = get_font(14, bold=True)
    f_rule = get_font(17, bold=True)

    title = str(concept.get("title", "SYSTEM ARCHITECTURE")).upper()
    category = str(concept.get("category", "ENGINEERING")).upper()
    ca = concept.get("concept_a", {})
    cb = concept.get("concept_b", {})
    golden_rule = str(concept.get("golden_rule", "Choose the right tool for the engineering requirements."))
    tradeoffs = concept.get("tradeoff_table", [])

    name_a = str(ca.get("name", "Option A")).upper()
    best_a = str(ca.get("best_for", "General use"))
    analogy_a = str(ca.get("analogy", ""))

    name_b = str(cb.get("name", "Option B")).upper()
    best_b = str(cb.get("best_for", "Specialized use"))
    analogy_b = str(cb.get("analogy", ""))

    for frame_idx in range(total_frames):
        img = Image.new("RGB", (w, h), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # Subtle dark tech grid
        for x in range(0, w, 60):
            draw.line([(x, 0), (x, h)], fill=(15, 23, 42), width=1)
        for y in range(0, h, 60):
            draw.line([(0, y), (w, y)], fill=(15, 23, 42), width=1)

        # Top Badge
        draw.rounded_rectangle([70, 40, 310, 75], radius=6, fill=(30, 41, 59))
        draw.text((85, 47), f"NEUBENCH • {category[:18]}", fill=CYAN_ACCENT, font=f_tag)

        # Header Title
        draw.text((70, 88), title[:40], fill=WHITE, font=f_title)
        draw.text((70, 136), "Head-to-head architectural mechanics & production rules of thumb", fill=MUTED, font=f_sub)

        # Alternating subtle glow phases
        pulse_a = math.sin((frame_idx / total_frames) * math.pi * 2)
        glow_a = int(180 + 75 * max(0, pulse_a))
        col_a = (56, 189, max(140, min(255, glow_a)))

        pulse_b = math.sin(((frame_idx + total_frames // 2) / total_frames) * math.pi * 2)
        glow_b = int(180 + 75 * max(0, pulse_b))
        col_b = (52, max(140, min(255, glow_b)), 153)

        # Left Column Card (Concept A)
        draw.rounded_rectangle([70, 180, 520, 480], radius=14, fill=CARD_BG, outline=col_a, width=2)
        draw.rounded_rectangle([70, 180, 520, 230], radius=14, fill=(24, 32, 48))
        draw.text((95, 192), f"⚡ {name_a[:22]}", fill=CYAN_ACCENT, font=f_sec)

        draw.text((95, 245), "HOW IT WORKS:", fill=MUTED, font=f_tag)
        # Wrap mechanism text
        words_a = str(ca.get("how_it_works", ""))[:120].split()
        line1_a = " ".join(words_a[:7])
        line2_a = " ".join(words_a[7:14])
        line3_a = " ".join(words_a[14:21])
        draw.text((95, 270), line1_a, fill=WHITE, font=f_small)
        draw.text((95, 292), line2_a, fill=WHITE, font=f_small)
        draw.text((95, 314), line3_a, fill=WHITE, font=f_small)

        draw.text((95, 350), "BEST FOR:", fill=AMBER_ACCENT, font=f_tag)
        words_best_a = best_a[:90].split()
        draw.text((95, 375), " ".join(words_best_a[:7]), fill=WHITE, font=f_small)
        draw.text((95, 397), " ".join(words_best_a[7:14]), fill=WHITE, font=f_small)

        # Right Column Card (Concept B)
        draw.rounded_rectangle([560, 180, 1010, 480], radius=14, fill=CARD_BG, outline=col_b, width=2)
        draw.rounded_rectangle([560, 180, 1010, 230], radius=14, fill=(20, 36, 32))
        draw.text((585, 192), f"🌿 {name_b[:22]}", fill=EMERALD_ACCENT, font=f_sec)

        draw.text((585, 245), "HOW IT WORKS:", fill=MUTED, font=f_tag)
        words_b = str(cb.get("how_it_works", ""))[:120].split()
        line1_b = " ".join(words_b[:7])
        line2_b = " ".join(words_b[7:14])
        line3_b = " ".join(words_b[14:21])
        draw.text((585, 270), line1_b, fill=WHITE, font=f_small)
        draw.text((585, 292), line2_b, fill=WHITE, font=f_small)
        draw.text((585, 314), line3_b, fill=WHITE, font=f_small)

        draw.text((585, 350), "BEST FOR:", fill=AMBER_ACCENT, font=f_tag)
        words_best_b = best_b[:90].split()
        draw.text((585, 375), " ".join(words_best_b[:7]), fill=WHITE, font=f_small)
        draw.text((585, 397), " ".join(words_best_b[7:14]), fill=WHITE, font=f_small)

        # Center Comparison Scorecard Table
        draw.rounded_rectangle([70, 510, 1010, 830], radius=12, fill=(13, 17, 23), outline=BORDER_COLOR, width=2)
        draw.rounded_rectangle([70, 510, 1010, 555], radius=12, fill=(22, 27, 34))
        draw.text((95, 522), "METRIC / FACTOR", fill=MUTED, font=f_tag)
        draw.text((430, 522), name_a[:16], fill=CYAN_ACCENT, font=f_tag)
        draw.text((740, 522), name_b[:16], fill=EMERALD_ACCENT, font=f_tag)

        row_y = 575
        for r_idx, row in enumerate(tradeoffs[:4]):
            metric_label = row[0] if len(row) > 0 else f"Metric {r_idx+1}"
            val_a = row[1] if len(row) > 1 else "-"
            val_b = row[2] if len(row) > 2 else "-"

            # Alternate row background
            if r_idx % 2 == 1:
                draw.rectangle([72, row_y - 8, 1008, row_y + 44], fill=(17, 24, 39))

            draw.text((95, row_y + 4), metric_label[:28], fill=WHITE, font=f_bold)
            draw.text((430, row_y + 4), val_a[:24], fill=(186, 230, 253), font=f_small)
            draw.text((740, row_y + 4), val_b[:24], fill=(167, 243, 208), font=f_small)
            row_y += 56

        # Bottom Golden Rule Bar (Animated pulse on border)
        rule_border = (56, 189, 248) if (frame_idx % 8 < 4) else (52, 211, 153)
        draw.rounded_rectangle([70, 860, 1010, 960], radius=12, fill=(15, 23, 42), outline=rule_border, width=2)
        draw.text((95, 875), "💡 GOLDEN ENGINEERING RULE:", fill=AMBER_ACCENT, font=f_tag)
        rule_words = golden_rule[:110].split()
        draw.text((95, 905), " ".join(rule_words[:14]), fill=WHITE, font=f_rule)
        if len(rule_words) > 14:
            draw.text((95, 930), " ".join(rule_words[14:26]), fill=WHITE, font=f_small)

        # Footer
        draw.text((70, 995), "NeuBench Educational Architecture Series", fill=MUTED, font=f_sub)
        draw.text((780, 995), "app.neubench.workers.dev", fill=CYAN_ACCENT, font=f_sub)

        frames.append(img)

    # Compile High-Quality Looping GIF
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=65,
        loop=0,
        optimize=True
    )

    compiled_mp4 = compile_frames_to_mp4(frames, "temp_concept", fps, mp4_path)
    return gif_path, (compiled_mp4 or "")


def generate_concept_visual(concept: Dict[str, Any]) -> str:
    """
    Main helper to generate and return a crisp looping GIF for any educational concept.
    """
    import hashlib, re
    title = concept.get("title", "concept")
    raw_slug = re.sub(r'[^a-zA-Z0-9_]', '_', title.strip().lower())
    clean_slug = re.sub(r'_+', '_', raw_slug)[:25].strip('_')
    content_hash = hashlib.md5(f"{title}_{concept.get('category', '')}".encode()).hexdigest()[:8]
    unique_base = f"{clean_slug}_{content_hash}" if clean_slug else f"concept_{content_hash}"

    gif_path, mp4_path = render_dynamic_concept_comparison(concept, output_base_name=unique_base)
    return gif_path

