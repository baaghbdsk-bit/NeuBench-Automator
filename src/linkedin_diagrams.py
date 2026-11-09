"""Animated LinkedIn diagrams and dynamic execution flow infographics.

Produces clean, high-framerate looping GIFs showing sequential architecture pipelines
with traveling energy pulses, active stage lighting, and topic-specific mechanics.
"""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

from src.linkedin_visuals import (
    ACCENT_NAVY,
    ACCENT_TERRACOTTA,
    ACCENT_AMBER,
    INK,
    LINE_ON_PAPER,
    MUTED_ON_PAPER,
    OUTPUT_DIR,
    PAPER,
    PAPER_CARD,
    PAPER_SOFT,
    draw_tracked,
    fit_wrapped,
    get_font,
)

ACCENT = ACCENT_NAVY
ACCENT_LIGHT = (56, 189, 248)
MUTED_ON_DARK = (148, 163, 184)
WHITE = (248, 250, 252)


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_size: int = 18, min_size: int = 14, kind: str = "sans") -> Any:
    for s in range(max_size, min_size - 1, -1):
        f = get_font(s, kind)
        if draw.textlength(text, font=f) <= max_w:
            return f
    return get_font(min_size, kind)

W, H = 1080, 1350
MARGIN = 92
CONTENT_W = W - (MARGIN * 2)
HEADER_H = 380
CARD_X = MARGIN
CARD_W = CONTENT_W
RAIL_X = 60
CARD_TEXT_X = 176
ICON_X = 888

DEFAULT_TRANSFORMER_STAGES: List[Dict[str, str]] = [
    {
        "kicker": "STEP 01",
        "title": "Tokenize",
        "detail": "The sentence becomes tokens: The / cat / sat / on / the.",
        "icon": "tokens",
    },
    {
        "kicker": "STEP 02",
        "title": "Embed",
        "detail": "Each token becomes a vector, a list of numbers learned from data.",
        "icon": "embedding",
    },
    {
        "kicker": "STEP 03",
        "title": "Add position",
        "detail": "Order signals are added so word order stays intact.",
        "icon": "position",
    },
    {
        "kicker": "STEP 04",
        "title": "Attention",
        "detail": "Each token weighs every other token and pulls in context.",
        "icon": "attention",
    },
    {
        "kicker": "STEP 05",
        "title": "Feed-forward",
        "detail": "A small network refines each position on its own.",
        "icon": "ff",
    },
    {
        "kicker": "STEP 06",
        "title": "Predict",
        "detail": "The model scores the vocabulary and picks the next token.",
        "icon": "predict",
    },
]


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
    return cleaned.strip("_")[:40] or "pipeline_flow"


def _mix(a: Tuple[int, int, int], b: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(a[index] + (b[index] - a[index]) * t) for index in range(3))


def _activation(travel: float, index: int, card_count: int) -> float:
    center = (index + 0.5) / max(1, card_count)
    distance = abs(travel - center) * card_count
    if distance <= 0.45:
        return 1.0
    return max(0.0, 1.0 - (distance - 0.45) / 0.35)


def _tracked_text_width(draw: ImageDraw.ImageDraw, text: str, font: Any, tracking: int) -> int:
    return int(sum(draw.textlength(ch, font=font) for ch in text) + tracking * max(0, len(text) - 1))


def _compute_layout(card_count: int) -> Tuple[int, int, int]:
    count = max(3, min(6, card_count))
    if count == 6:
        card_h = 108
        card_gap = 16
        pipeline_top = 430
    elif count == 5:
        card_h = 122
        card_gap = 18
        pipeline_top = 430
    elif count == 4:
        card_h = 138
        card_gap = 22
        pipeline_top = 440
    else:  # count == 3
        card_h = 165
        card_gap = 26
        pipeline_top = 460
    return card_h, card_gap, pipeline_top


def _card_top(index: int, card_h: int, card_gap: int, pipeline_top: int) -> int:
    return pipeline_top + index * (card_h + card_gap)


def _card_center(index: int, card_h: int, card_gap: int, pipeline_top: int) -> int:
    return _card_top(index, card_h, card_gap, pipeline_top) + card_h // 2


def _draw_header(draw: ImageDraw.ImageDraw, title: str, kicker: str, subtitle: str, card_count: int) -> None:
    draw.rectangle([0, 0, W, HEADER_H], fill=INK)
    draw.rectangle([MARGIN, 80, MARGIN + 64, 88], fill=ACCENT)
    
    clean_kicker = (kicker or "SYSTEM FLOW").upper()[:28]
    draw_tracked(draw, (MARGIN, 104), clean_kicker, get_font(18, "sans_bold"), ACCENT_LIGHT, 3)
    
    meta_font = get_font(13, "sans_bold")
    meta = f"{card_count} STAGES / 1 PASS"
    meta_width = _tracked_text_width(draw, meta, meta_font, 2)
    draw_tracked(draw, (W - MARGIN - meta_width, 106), meta, meta_font, MUTED_ON_DARK, 2)

    title_font, lines = fit_wrapped(
        draw,
        title[:55],
        CONTENT_W,
        max_lines=2,
        max_size=60,
        min_size=42,
        kind="serif_bold",
    )
    y = 150
    for line in lines:
        draw.text((MARGIN, y), line, font=title_font, fill=WHITE)
        y += title_font.size + 6

    subhead_font = get_font(24, "sans")
    clean_sub = subtitle[:70] if subtitle else "Step-by-step end-to-end execution flow."
    draw.text((MARGIN, y + 10), clean_sub, font=subhead_font, fill=MUTED_ON_DARK)


def _draw_rail(draw: ImageDraw.ImageDraw, travel: float, fade: float, card_count: int, card_h: int, card_gap: int, pipeline_top: int) -> None:
    first = _card_center(0, card_h, card_gap, pipeline_top)
    last = _card_center(card_count - 1, card_h, card_gap, pipeline_top)
    pulse_y = first + (last - first) * max(0.0, min(1.0, travel))
    draw.line([(RAIL_X, first), (RAIL_X, last)], fill=LINE_ON_PAPER, width=3)
    if pulse_y > first:
        draw.line([(RAIL_X, first), (RAIL_X, pulse_y)], fill=_mix(LINE_ON_PAPER, ACCENT, fade), width=3)

    for index in range(card_count):
        act = _activation(travel, index, card_count) * fade
        color = _mix(LINE_ON_PAPER, ACCENT, act)
        width = 3 if act > 0.55 else 2
        center_y = _card_center(index, card_h, card_gap, pipeline_top)
        draw.line([(RAIL_X, center_y), (CARD_X, center_y)], fill=color, width=width)


def _draw_pulse(draw: ImageDraw.ImageDraw, travel: float, fade: float, card_count: int, card_h: int, card_gap: int, pipeline_top: int) -> None:
    if fade <= 0.02:
        return
    first = _card_center(0, card_h, card_gap, pipeline_top)
    last = _card_center(card_count - 1, card_h, card_gap, pipeline_top)
    pulse_y = first + (last - first) * max(0.0, min(1.0, travel))
    halo = _mix(PAPER, ACCENT_LIGHT, fade)
    draw.ellipse([RAIL_X - 18, pulse_y - 18, RAIL_X + 18, pulse_y + 18], fill=halo)
    draw.ellipse([RAIL_X - 10, pulse_y - 10, RAIL_X + 10, pulse_y + 10], fill=ACCENT)
    draw.ellipse([RAIL_X - 4, pulse_y - 4, RAIL_X + 4, pulse_y + 4], fill=WHITE)


def _draw_tokens(draw: ImageDraw.ImageDraw, x: int, y: int, act: float) -> None:
    widths = (30, 34, 26, 34)
    cursor = x - 58
    for width in widths:
        color = _mix(LINE_ON_PAPER, ACCENT, act)
        draw.rounded_rectangle([cursor, y - 6, cursor + width, y + 6], radius=5, fill=color)
        cursor += width + 8


def _draw_embedding(draw: ImageDraw.ImageDraw, x: int, y: int, act: float) -> None:
    heights = (18, 36, 26, 46, 32)
    cursor = x - 50
    for height in heights:
        color = _mix(LINE_ON_PAPER, ACCENT, act)
        draw.rounded_rectangle([cursor, y - height // 2, cursor + 10, y + height // 2], radius=4, fill=color)
        cursor += 18


def _draw_position(draw: ImageDraw.ImageDraw, x: int, y: int, act: float) -> None:
    points = []
    for step in range(41):
        px = x - 54 + step * 3
        py = y - int(math.sin(step / 40 * math.pi * 2) * 18)
        points.append((px, py))
    color = _mix(LINE_ON_PAPER, ACCENT, act)
    draw.line(points, fill=color, width=3)
    for step in (6, 20, 34):
        px = x - 54 + step * 3
        py = y - int(math.sin(step / 40 * math.pi * 2) * 18)
        draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=color)


def _draw_attention(draw: ImageDraw.ImageDraw, x: int, y: int, act: float) -> None:
    nodes = [(x - 34, y - 16), (x - 12, y + 18), (x + 12, y - 18), (x + 34, y + 14)]
    line_color = _mix(LINE_ON_PAPER, ACCENT, act * 0.9)
    node_color = _mix(LINE_ON_PAPER, ACCENT, act)
    for start in range(len(nodes)):
        for end in range(start + 1, len(nodes)):
            draw.line([nodes[start], nodes[end]], fill=line_color, width=2)
    for px, py in nodes:
        draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=node_color)


def _draw_ff(draw: ImageDraw.ImageDraw, x: int, y: int, act: float) -> None:
    left = [(x - 38, y - 22), (x - 38, y), (x - 38, y + 22)]
    right = [(x + 22, y - 30), (x + 22, y - 10), (x + 22, y + 10), (x + 22, y + 30)]
    edge_color = _mix(LINE_ON_PAPER, ACCENT, act * 0.55)
    node_color = _mix(LINE_ON_PAPER, ACCENT, act)
    for a in left:
        for b in right:
            draw.line([a, b], fill=edge_color, width=1)
    for px, py in left:
        draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=node_color)
    for px, py in right:
        draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=node_color)


def _draw_predict(draw: ImageDraw.ImageDraw, x: int, y: int, act: float) -> None:
    widths = (80, 56, 34)
    for index, width in enumerate(widths):
        top = y - 20 + index * 18
        color = _mix(LINE_ON_PAPER, ACCENT, act if index == 0 else act * 0.45)
        draw.rounded_rectangle([x - 44, top, x - 44 + width, top + 8], radius=4, fill=color)


_ICONS = {
    "tokens": _draw_tokens,
    "embedding": _draw_embedding,
    "position": _draw_position,
    "attention": _draw_attention,
    "ff": _draw_ff,
    "predict": _draw_predict,
}


def _draw_card(
    draw: ImageDraw.ImageDraw,
    index: int,
    act: float,
    stage: Dict[str, str],
    card_count: int,
    card_h: int,
    card_gap: int,
    pipeline_top: int,
) -> None:
    top = _card_top(index, card_h, card_gap, pipeline_top)
    bottom = top + card_h
    fill = _mix(PAPER_SOFT, (232, 238, 252), act)
    border = _mix(LINE_ON_PAPER, ACCENT, act)
    width = 3 if act > 0.5 else 1
    draw.rounded_rectangle([CARD_X, top, CARD_X + CARD_W, bottom], radius=18, fill=fill, outline=border, width=width)

    circle_x = CARD_X + 36
    circle_y = top + card_h // 2
    circle_fill = _mix(PAPER, ACCENT, act)
    circle_text = WHITE if act > 0.5 else MUTED_ON_PAPER
    draw.ellipse([circle_x - 22, circle_y - 22, circle_x + 22, circle_y + 22], fill=circle_fill, outline=border)
    number_font = get_font(22, "sans_bold")
    number = str(index + 1)
    number_w = draw.textlength(number, font=number_font)
    draw.text((circle_x - number_w / 2, circle_y - 14), number, font=number_font, fill=circle_text)

    kicker_font = get_font(13, "sans_bold")
    kicker_text = str(stage.get("kicker") or f"STEP {index+1:02d}").upper()
    draw_tracked(draw, (CARD_TEXT_X, top + 14), kicker_text, kicker_font, _mix(MUTED_ON_PAPER, ACCENT, act), 2)
    
    title_font = get_font(28 if card_h >= 120 else 24, "sans_bold")
    stage_title = str(stage.get("title") or f"Stage {index+1}")[:26]
    draw.text((CARD_TEXT_X, top + 32), stage_title, font=title_font, fill=INK)
    
    detail_text = str(stage.get("detail") or stage.get("desc") or "")[:70]
    detail_font = fit_font(draw, detail_text, 596, 18, 14, "sans")
    draw.text((CARD_TEXT_X, top + (68 if card_h >= 120 else 62)), detail_text, font=detail_font, fill=MUTED_ON_PAPER)

    icon_key = stage.get("icon", "")
    icon_fn = _ICONS.get(icon_key)
    if not icon_fn:
        # Default icon rotation if unknown
        icon_keys = list(_ICONS.keys())
        icon_fn = _ICONS[icon_keys[index % len(icon_keys)]]
    icon_fn(draw, ICON_X, circle_y, act)


def _draw_footer(draw: ImageDraw.ImageDraw) -> None:
    draw.line([(MARGIN, 1214), (W - MARGIN, 1214)], fill=LINE_ON_PAPER, width=1)
    draw_tracked(draw, (MARGIN, 1240), "NEUBENCH", get_font(14, "sans_bold"), MUTED_ON_PAPER, 3)
    label = "ENGINEERING BLUEPRINTS"
    font = get_font(14, "sans_bold")
    width = _tracked_text_width(draw, label, font, 2)
    draw_tracked(draw, (W - MARGIN - width, 1240), label, font, MUTED_ON_PAPER, 2)


def render_frame_dynamic(
    progress: float,
    stages: List[Dict[str, str]],
    title: str,
    kicker: str,
    subtitle: str,
) -> Image.Image:
    image = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(image)
    card_count = max(3, min(6, len(stages)))
    active_stages = stages[:card_count]
    card_h, card_gap, pipeline_top = _compute_layout(card_count)

    _draw_header(draw, title, kicker, subtitle, card_count)
    travel = min(1.0, max(0.0, progress) / 0.82)
    fade = 1.0 if progress <= 0.9 else max(0.0, 1.0 - (progress - 0.9) / 0.1)
    _draw_rail(draw, travel, fade, card_count, card_h, card_gap, pipeline_top)
    for index, stage in enumerate(active_stages):
        _draw_card(draw, index, _activation(travel, index, card_count) * fade, stage, card_count, card_h, card_gap, pipeline_top)
    _draw_pulse(draw, travel, fade, card_count, card_h, card_gap, pipeline_top)
    _draw_footer(draw)
    return image


def render_flow_diagram_gif(
    pipeline_spec: Dict[str, Any],
    base_name: Optional[str] = None,
    frames: int = 48,
    duration: int = 75,
) -> Dict[str, Any]:
    """
    Renders a topic-specific dynamic flow GIF with travelling pulse pointer and step cards.
    Guarantees zero hardcoded stages: strictly derived from pipeline_spec.
    """
    title = str(pipeline_spec.get("title") or "System Execution Flow").strip()
    kicker = str(pipeline_spec.get("kicker") or "SYSTEM PIPELINE").strip()
    subtitle = str(pipeline_spec.get("subtitle") or "Step-by-step architectural breakdown").strip()
    raw_stages = pipeline_spec.get("stages") or pipeline_spec.get("steps") or []
    if not raw_stages:
        raise ValueError("Cannot render dynamic flow GIF: pipeline_spec has no stages/steps.")

    stages = []
    icon_list = ["tokens", "embedding", "position", "attention", "ff", "predict"]
    for idx, s in enumerate(raw_stages[:6]):
        stitle = str(s.get("title") or s.get("label") or s.get("name") or f"Stage {idx+1}").strip()
        sdetail = str(s.get("detail") or s.get("desc") or s.get("description") or "").strip()
        sicon = s.get("icon") or icon_list[idx % len(icon_list)]
        skicker = str(s.get("kicker") or f"STEP {idx+1:02d}").strip()
        stages.append({
            "kicker": skicker,
            "title": stitle,
            "detail": sdetail,
            "icon": sicon,
        })

    if not base_name:
        digest = hashlib.md5(f"{title}_{len(stages)}".encode("utf-8")).hexdigest()[:8]
        base_name = f"flow_{_slug(title)}_{digest}"

    folder = OUTPUT_DIR / base_name
    folder.mkdir(parents=True, exist_ok=True)

    images = [render_frame_dynamic(idx / frames, stages, title, kicker, subtitle) for idx in range(frames)]
    preview_path = folder / f"{base_name}_first_frame.png"
    images[0].save(preview_path, "PNG")

    gif_path = folder / f"{base_name}.gif"
    images[0].save(
        gif_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return {
        "folder": str(folder),
        "path": str(gif_path),
        "gif_path": str(gif_path),
        "preview_path": str(preview_path),
        "frames": frames,
        "duration_ms": duration,
        "title": title,
        "stage_count": len(stages),
    }


def build_topic_flow_spec(topic_title: str, summary: str = "", steps: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Helper to convert structured steps or dynamic topic info into a pipeline_spec."""
    clean_title = topic_title.strip()
    if steps and len(steps) >= 3:
        stages = []
        for idx, st in enumerate(steps[:6], start=1):
            stages.append({
                "kicker": f"STEP {idx:02d}",
                "title": str(st.get("label") or st.get("title") or st.get("name") or f"Step {idx}")[:24],
                "detail": str(st.get("desc") or st.get("detail") or st.get("description") or "")[:70],
                "icon": st.get("icon") or "attention",
            })
        return {
            "title": clean_title,
            "kicker": "EXECUTION FLOW",
            "subtitle": (summary[:70] if summary else "Sequential execution stages").strip(),
            "stages": stages,
        }

    # Derive 4 stages dynamically from the topic title/summary
    return {
        "title": clean_title,
        "kicker": "ARCHITECTURE FLOW",
        "subtitle": (summary[:70] if summary else f"How {clean_title[:45]} operates end-to-end").strip(),
        "stages": [
            {"kicker": "STEP 01", "title": "Input Dispatch", "detail": f"Ingests payload for {clean_title[:28]}", "icon": "tokens"},
            {"kicker": "STEP 02", "title": "Protocol Transform", "detail": "Validates schemas, applies codecs & state", "icon": "embedding"},
            {"kicker": "STEP 03", "title": "Core Processing", "detail": "Executes logic with zero redundant copies", "icon": "attention"},
            {"kicker": "STEP 04", "title": "Sink & Output", "detail": "Commits state and streams response to client", "icon": "predict"},
        ]
    }


def render_transformer_flow_gif(
    base_name: str = "transformer_flow",
    frames: int = 60,
    duration: int = 80,
) -> Dict[str, Any]:
    """Backwards-compatible transformer diagram renderer."""
    return render_flow_diagram_gif(
        {
            "title": "How a Transformer Reads a Sentence",
            "kicker": "TRANSFORMER FLOW",
            "subtitle": "One forward pass, token by token.",
            "stages": DEFAULT_TRANSFORMER_STAGES,
        },
        base_name=base_name,
        frames=frames,
        duration=duration,
    )


def draw_dashed_line(draw: ImageDraw.ImageDraw, start: Tuple[int, int], end: Tuple[int, int], color: Tuple[int, int, int], dash_len: int = 8, gap: int = 6):
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)
    if dist == 0:
        return
    vx = dx / dist
    vy = dy / dist
    curr = 0.0
    while curr < dist:
        seg_end = min(curr + dash_len, dist)
        p1 = (x1 + vx * curr, y1 + vy * curr)
        p2 = (x1 + vx * seg_end, y1 + vy * seg_end)
        draw.line([p1, p2], fill=color, width=2)
        curr += dash_len + gap


def render_editorial_architecture_frame(progress: float, spec: dict) -> Image.Image:
    """Renders a single 1080x1350 frame of the editorial multi-panel architecture flow."""
    im = Image.new("RGB", (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(im)

    title = str(spec.get("title", "System Architecture")).strip()
    subtitle = str(spec.get("subtitle", "Sequential execution flow and production trade-offs")).strip()

    # 1. Top Header
    draw.rounded_rectangle([MARGIN, 44, MARGIN + 280, 78], radius=6, fill=(241, 245, 249))
    draw.text((MARGIN + 16, 52), "// NEUBENCH ARCHITECTURE", fill=(14, 116, 144), font=get_font(14, "sans_bold"))

    draw.text((MARGIN, 92), f"Understanding {title[:32]}", fill=(15, 23, 42), font=get_font(38, "serif_bold"))
    draw.text((MARGIN, 146), f"{subtitle[:70]} · Save this.", fill=(71, 85, 105), font=get_font(20, "sans"))

    draw_dashed_line(draw, (MARGIN, 195), (W - MARGIN, 195), (203, 213, 225))

    # 2. Section 1: Architecture Pipeline & Moving Flow Pointer
    draw.text((MARGIN, 210), "1. SYSTEM FLOW & ROUTING MECHANICS", fill=(15, 23, 42), font=get_font(21, "sans_bold"))

    # Ingestion Box (Left)
    in_box = [MARGIN, 260, MARGIN + 210, 350]
    draw.rounded_rectangle(in_box, radius=10, fill=(248, 250, 252), outline=(226, 232, 240), width=2)
    in_label = str(spec.get("input_label", "INPUT STREAM"))[:20]
    draw.text((MARGIN + 20, 276), in_label, fill=(15, 23, 42), font=get_font(16, "sans_bold"))
    draw.text((MARGIN + 20, 305), "Context stream payload", fill=(71, 85, 105), font=get_font(14, "sans"))

    # Router Box (Middle)
    r_box = [MARGIN + 290, 245, MARGIN + 530, 365]
    draw.rounded_rectangle(r_box, radius=12, fill=(15, 23, 42), outline=(226, 232, 240), width=2)
    r_label = str(spec.get("router_label", "Top-K Router"))[:22]
    draw.text((MARGIN + 310, 268), r_label, fill=(255, 255, 255), font=get_font(17, "sans_bold"))
    draw.text((MARGIN + 310, 298), "Softmax gate scores", fill=(148, 163, 184), font=get_font(14, "sans"))
    draw.text((MARGIN + 310, 322), "Selects active paths", fill=(245, 158, 11), font=get_font(13, "sans_bold"))

    # Arrow 1: Ingestion -> Router
    draw.line([(MARGIN + 210, 305), (MARGIN + 290, 305)], fill=(203, 213, 225), width=3)
    draw.polygon([(MARGIN + 288, 305), (MARGIN + 278, 299), (MARGIN + 278, 311)], fill=(203, 213, 225))

    # Target Component Boxes (Right side)
    comps = spec.get("components", [
        {"name": "Expert 1", "role": "Math & Code", "active": False},
        {"name": "Expert 2", "role": "Reasoning", "active": True, "score": "0.38"},
        {"name": "Expert 3", "role": "Language", "active": False},
        {"name": "Expert 4", "role": "Knowledge", "active": True, "score": "0.42"},
    ])

    comp_start_y = 230
    comp_h = 58
    comp_gap = 14
    comp_x0 = MARGIN + 610
    comp_x1 = W - MARGIN

    active_targets = []
    for idx, c in enumerate(comps[:4]):
        cy0 = comp_start_y + idx * (comp_h + comp_gap)
        cy1 = cy0 + comp_h
        is_active = c.get("active", False)
        if is_active:
            active_targets.append((comp_x0, (cy0 + cy1) // 2))

        # Branching arrow from Router (MARGIN + 530, 305) to (comp_x0, (cy0 + cy1)//2)
        mid_y = (cy0 + cy1) // 2
        draw.line([(MARGIN + 530, 305), (MARGIN + 570, mid_y)], fill=(203, 213, 225), width=2)
        draw.line([(MARGIN + 570, mid_y), (comp_x0, mid_y)], fill=(203, 213, 225), width=2)
        draw.polygon([(comp_x0, mid_y), (comp_x0 - 8, mid_y - 5), (comp_x0 - 8, mid_y + 5)], fill=(203, 213, 225))

        # Card highlight if active and in routing phase
        card_highlight = is_active and (progress >= 0.40)
        c_fill = (255, 251, 235) if card_highlight else (248, 250, 252)
        c_outline = (245, 158, 11) if card_highlight else (226, 232, 240)
        c_w = 3 if card_highlight else 2
        draw.rounded_rectangle([comp_x0, cy0, comp_x1, cy1], radius=8, fill=c_fill, outline=c_outline, width=c_w)

        c_name = str(c.get("name", f"Engine {idx+1}"))[:20]
        c_role = str(c.get("role", "Execution stage"))[:24]
        draw.text((comp_x0 + 16, cy0 + 10), c_name, fill=(15, 23, 42), font=get_font(15, "sans_bold"))
        draw.text((comp_x0 + 16, cy0 + 32), c_role, fill=(71, 85, 105), font=get_font(13, "sans"))

        if card_highlight and c.get("score"):
            score_txt = f"[{c['score']} ACTIVE]"
            draw.text((comp_x1 - 110, cy0 + 20), score_txt, fill=(245, 158, 11), font=get_font(12, "sans_bold"))

    # Moving Pulse Animation (Pointing from where to where it's moving, what calls next)
    pulse_radius = 8
    halo_radius = 16
    if progress < 0.35:
        # Phase 1: Input -> Router
        t = progress / 0.35
        px = (MARGIN + 210) + ((MARGIN + 290) - (MARGIN + 210)) * t
        py = 305
        draw.ellipse([px - halo_radius, py - halo_radius, px + halo_radius, py + halo_radius], fill=(254, 243, 199))
        draw.ellipse([px - pulse_radius, py - pulse_radius, px + pulse_radius, py + pulse_radius], fill=(245, 158, 11))
    elif progress < 0.75:
        # Phase 2: Router -> Active Components
        t = (progress - 0.35) / 0.40
        for tx, ty in active_targets:
            if t < 0.4:
                sub_t = t / 0.4
                px = (MARGIN + 530) + ((MARGIN + 570) - (MARGIN + 530)) * sub_t
                py = 305 + (ty - 305) * sub_t
            else:
                sub_t = (t - 0.4) / 0.6
                px = (MARGIN + 570) + (tx - (MARGIN + 570)) * sub_t
                py = ty
            draw.ellipse([px - halo_radius, py - halo_radius, px + halo_radius, py + halo_radius], fill=(254, 243, 199))
            draw.ellipse([px - pulse_radius, py - pulse_radius, px + pulse_radius, py + pulse_radius], fill=(245, 158, 11))
    else:
        # Phase 3: Active target executing & emitting output
        t = (progress - 0.75) / 0.25
        for tx, ty in active_targets:
            px = comp_x1 - 20
            py = ty
            pulse_size = pulse_radius + int(math.sin(t * math.pi) * 4)
            draw.ellipse([px - pulse_size, py - pulse_size, px + pulse_size, py + pulse_size], fill=(16, 185, 129))

    # 3. Section 2: Production Metrics & Trade-offs
    draw_dashed_line(draw, (MARGIN, 545), (W - MARGIN, 545), (203, 213, 225))
    draw.text((MARGIN, 560), "2. PRODUCTION RESOURCE PROFILE & METRICS", fill=(15, 23, 42), font=get_font(21, "sans_bold"))

    metrics = spec.get("metrics", [
        {"label": "Active Compute per Token", "val": "13B FLOPs (28% of capacity)", "pct": 0.28, "color": "emerald"},
        {"label": "Total Model Footprint", "val": "47B Parameters across experts", "pct": 0.92, "color": "slate"},
        {"label": "GPU Memory Required", "val": "~93 GB in 16-bit precision", "pct": 0.85, "color": "amber"},
    ])

    m_start_y = 600
    bar_w = CONTENT_W
    bar_h = 24
    for m_idx, m in enumerate(metrics[:3]):
        my = m_start_y + m_idx * 68
        draw.text((MARGIN, my), str(m["label"])[:32], fill=(15, 23, 42), font=get_font(15, "sans_bold"))
        draw.text((W - MARGIN - 260, my), str(m["val"])[:32], fill=(71, 85, 105), font=get_font(14, "sans"))

        draw.rounded_rectangle([MARGIN, my + 26, W - MARGIN, my + 26 + bar_h], radius=6, fill=(241, 245, 249))

        ease = min(1.0, progress * 1.4)
        target_pct = float(m.get("pct", 0.5)) * ease
        fill_w = int(bar_w * target_pct)
        col = (16, 185, 129) if m.get("color") == "emerald" else ((245, 158, 11) if m.get("color") == "amber" else (71, 85, 105))
        if fill_w > 8:
            draw.rounded_rectangle([MARGIN, my + 26, MARGIN + fill_w, my + 26 + bar_h], radius=6, fill=col)

    # 4. Section 3: End-to-End Execution Lifecycle
    draw_dashed_line(draw, (MARGIN, 825), (W - MARGIN, 825), (203, 213, 225))
    draw.text((MARGIN, 840), "3. STEP-BY-STEP EXECUTION LIFECYCLE", fill=(15, 23, 42), font=get_font(21, "sans_bold"))

    steps = spec.get("steps", [
        {"num": "1", "name": "Token Ingestion", "desc": "Context token enters transformer layer"},
        {"num": "2", "name": "Softmax Scoring", "desc": "Gating network computes expert probability weights"},
        {"num": "3", "name": "Sparse Dispatch", "desc": "Only top-2 chosen experts execute compute; others idle"},
        {"num": "4", "name": "Weighted Combine", "desc": "Outputs recombined and normalized back to residual bus"}
    ])

    s_start_y = 880
    card_h = 70
    card_gap = 12
    active_step_idx = int(progress * len(steps)) % len(steps)

    for s_idx, st in enumerate(steps[:4]):
        sy0 = s_start_y + s_idx * (card_h + card_gap)
        sy1 = sy0 + card_h
        is_cur = (s_idx == active_step_idx)

        s_bg = (255, 251, 235) if is_cur else (248, 250, 252)
        s_outline = (245, 158, 11) if is_cur else (226, 232, 240)
        s_w = 3 if is_cur else 1
        draw.rounded_rectangle([MARGIN, sy0, W - MARGIN, sy1], radius=10, fill=s_bg, outline=s_outline, width=s_w)

        badge_col = (245, 158, 11) if is_cur else (71, 85, 105)
        draw.rounded_rectangle([MARGIN + 16, sy0 + 16, MARGIN + 104, sy1 - 16], radius=6, fill=badge_col)
        draw.text((MARGIN + 28, sy0 + 26), f"STEP {st.get('num', s_idx+1)}", fill=(255, 255, 255), font=get_font(13, "sans_bold"))

        draw.text((MARGIN + 120, sy0 + 14), str(st.get("name", f"Stage {s_idx+1}"))[:28], fill=(15, 23, 42), font=get_font(16, "sans_bold"))
        draw.text((MARGIN + 120, sy0 + 38), str(st.get("desc", ""))[:65], fill=(71, 85, 105), font=get_font(14, "sans"))

    # 5. Footer
    draw_dashed_line(draw, (MARGIN, 1225), (W - MARGIN, 1225), (203, 213, 225))
    draw.text((MARGIN, 1245), "NeuBench Systems Architecture Series · app.neubench.workers.dev", fill=(71, 85, 105), font=get_font(14, "sans_bold"))
    draw.text((W - MARGIN - 140, 1245), "Save this 📌", fill=(245, 158, 11), font=get_font(14, "sans_bold"))

    return im


def render_editorial_architecture_gif(
    spec: Dict[str, Any],
    base_name: Optional[str] = None,
    frames: int = 40,
    duration: int = 75,
) -> Dict[str, Any]:
    """
    Renders an editorial 1080x1350 animated architecture flow GIF with traveling pulse,
    branching arrows, active component illumination, and lifecycle matrix.
    """
    title = str(spec.get("title") or "System Architecture").strip()
    if not base_name:
        digest = hashlib.md5(f"{title}_{len(spec.get('components', []))}".encode("utf-8")).hexdigest()[:8]
        base_name = f"arch_flow_{_slug(title)}_{digest}"

    folder = OUTPUT_DIR / base_name
    folder.mkdir(parents=True, exist_ok=True)

    images = [render_editorial_architecture_frame(idx / float(frames), spec) for idx in range(frames)]
    preview_path = folder / f"{base_name}_first_frame.png"
    images[0].save(preview_path, "PNG")

    gif_path = folder / f"{base_name}.gif"
    images[0].save(
        gif_path,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return {
        "folder": str(folder),
        "path": str(gif_path),
        "gif_path": str(gif_path),
        "preview_path": str(preview_path),
        "frames": frames,
        "duration_ms": duration,
        "title": title,
    }


def build_editorial_architecture_spec(
    title: str,
    summary: str = "",
    flow_steps: Optional[List[Dict[str, Any]]] = None,
    audience: str = "working_pro",
    ai_generator: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Constructs a topic-specific architecture specification for the editorial GIF renderer.
    Prefers AI-generated, 100% topic-specific components, metrics, and lifecycle steps.
    """
    clean_title = title.strip()

    if ai_generator is None:
        try:
            from src.ai_generator import AIGenerator
            ai_generator = AIGenerator()
        except Exception:
            ai_generator = None

    if ai_generator and hasattr(ai_generator, "generate_editorial_architecture_spec"):
        try:
            spec = ai_generator.generate_editorial_architecture_spec(
                title=clean_title,
                summary=summary,
                target_audience=audience
            )
            if spec and spec.get("components") and len(spec["components"]) >= 4:
                return spec
        except Exception as e:
            print(f"[linkedin_diagrams] AI spec generation notice: {e}")

    # Fallback to deterministic topic-aware spec generator
    if ai_generator and hasattr(ai_generator, "_build_deterministic_architecture_spec"):
        return ai_generator._build_deterministic_architecture_spec(clean_title, summary)

    parts = [p.strip() for p in re.split(r' vs | and | to | in | for | - ', clean_title, flags=re.I) if p.strip()]

    # Derive components tailored to topic
    if "moe" in clean_title.lower() or "mixture of experts" in clean_title.lower():
        input_label = "INPUT TOKENS"
        router_label = "Softmax Top-K Router"
        components = [
            {"name": "Expert 1: Math", "role": "Specialized arithmetic", "active": False},
            {"name": "Expert 2: Reasoning", "role": "Multi-hop logic", "active": True, "score": "0.38"},
            {"name": "Expert 3: Language", "role": "Syntax & translation", "active": False},
            {"name": "Expert 4: Domain", "role": "Code & knowledge", "active": True, "score": "0.42"},
        ]
        metrics = [
            {"label": "Active Compute per Token", "val": "13B FLOPs (28% of capacity)", "pct": 0.28, "color": "emerald"},
            {"label": "Total Model Weights", "val": "47B Parameters across experts", "pct": 0.92, "color": "slate"},
            {"label": "GPU Memory Required", "val": "~93 GB in 16-bit precision", "pct": 0.85, "color": "amber"},
        ]
    elif len(parts) >= 2:
        name_a, name_b = parts[0][:18], parts[1][:18]
        input_label = f"{name_a[:12].upper()} REQUEST"
        router_label = "Architecture Gateway"
        components = [
            {"name": f"{name_a} Primary", "role": "High-throughput path", "active": True, "score": "HOT"},
            {"name": f"{name_a} Replica", "role": "Read-scale worker", "active": False},
            {"name": f"{name_b} Engine", "role": "Specialized workload", "active": True, "score": "ASYNC"},
            {"name": f"{name_b} Storage", "role": "Persistent state layer", "active": False},
        ]
        metrics = [
            {"label": f"{name_a} Throughput", "val": "High sequential I/O", "pct": 0.82, "color": "emerald"},
            {"label": f"{name_b} Overhead", "val": "Random access memory footprint", "pct": 0.65, "color": "amber"},
            {"label": "Operational Complexity", "val": "Manageable failure domains", "pct": 0.45, "color": "slate"},
        ]
    else:
        input_label = f"{clean_title[:14].upper()}"
        router_label = "Execution Pipeline"
        components = [
            {"name": f"{clean_title[:12]} Parser", "role": "Validates payload invariants", "active": True, "score": "HOT"},
            {"name": "Core Engine", "role": "Executes domain transformation", "active": True, "score": "ACTIVE"},
            {"name": "Fast Cache", "role": "Low-latency memory path", "active": True, "score": "HIT"},
            {"name": "State Sink", "role": "Persistent commit layer", "active": False},
        ]
        metrics = [
            {"label": "Pipeline Throughput", "val": "Optimized execution bounds", "pct": 0.85, "color": "emerald"},
            {"label": "Memory Footprint", "val": "Zero memory leaks or copies", "pct": 0.35, "color": "slate"},
            {"label": "Tail Latency (p99)", "val": "Sub-millisecond guarantees", "pct": 0.70, "color": "amber"},
        ]

    steps = []
    if flow_steps and len(flow_steps) >= 3:
        for idx, fs in enumerate(flow_steps[:4], start=1):
            steps.append({
                "num": str(idx),
                "name": str(fs.get("label") or fs.get("title") or f"Stage {idx}")[:26],
                "desc": str(fs.get("desc") or fs.get("detail") or "")[:65],
            })
    else:
        steps = [
            {"num": "1", "name": "Payload Ingestion", "desc": f"Ingests payload for {clean_title[:24]}"},
            {"num": "2", "name": "Routing & Decision", "desc": "Evaluates invariants and selects target workers"},
            {"num": "3", "name": "Worker Execution", "desc": "Active target executes processing; others idle"},
            {"num": "4", "name": "State Commit", "desc": "Streams final response with minimal latency overhead"},
        ]

    return {
        "title": clean_title,
        "subtitle": (summary[:72] if summary else f"How {clean_title[:45]} operates end-to-end").strip(),
        "input_label": input_label,
        "router_label": router_label,
        "components": components,
        "steps": steps,
        "metrics": metrics,
    }
