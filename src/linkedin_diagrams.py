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
