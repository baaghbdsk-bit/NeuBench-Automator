"""Animated LinkedIn diagrams.

The transformer flow is a vertical pipeline: tokens, embeddings, position,
attention, feed-forward, and next-token prediction. A single pulse travels
through the six stages and the active card lights up. The loop is seamless.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageDraw

from src.linkedin_visuals import (
    ACCENT,
    ACCENT_LIGHT,
    INK,
    LINE_ON_PAPER,
    MUTED_ON_DARK,
    MUTED_ON_PAPER,
    OUTPUT_DIR,
    PAPER,
    PAPER_SOFT,
    WHITE,
    draw_tracked,
    fit_font,
    fit_wrapped,
    get_font,
)

W, H = 1080, 1350
MARGIN = 92
CONTENT_W = W - (MARGIN * 2)
HEADER_H = 380
CARD_X = MARGIN
CARD_W = CONTENT_W
CARD_H = 108
CARD_GAP = 16
PIPELINE_TOP = 430
RAIL_X = 60
CARD_TEXT_X = 176
ICON_X = 888
CARD_COUNT = 6

STAGES: List[Dict[str, str]] = [
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


def _mix(a: Tuple[int, int, int], b: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(a[index] + (b[index] - a[index]) * t) for index in range(3))


def _activation(travel: float, index: int) -> float:
    center = (index + 0.5) / CARD_COUNT
    distance = abs(travel - center) * CARD_COUNT
    if distance <= 0.45:
        return 1.0
    return max(0.0, 1.0 - (distance - 0.45) / 0.35)


def _tracked_text_width(draw: ImageDraw.ImageDraw, text: str, font: Any, tracking: int) -> int:
    return int(sum(draw.textlength(ch, font=font) for ch in text) + tracking * max(0, len(text) - 1))


def _card_top(index: int) -> int:
    return PIPELINE_TOP + index * (CARD_H + CARD_GAP)


def _card_center(index: int) -> int:
    return _card_top(index) + CARD_H // 2


def _draw_header(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle([0, 0, W, HEADER_H], fill=INK)
    draw.rectangle([MARGIN, 80, MARGIN + 64, 88], fill=ACCENT)
    draw_tracked(draw, (MARGIN, 104), "TRANSFORMER FLOW", get_font(18, "sans_bold"), ACCENT_LIGHT, 3)
    meta_font = get_font(13, "sans_bold")
    meta = "6 STAGES / 1 PASS"
    meta_width = _tracked_text_width(draw, meta, meta_font, 2)
    draw_tracked(draw, (W - MARGIN - meta_width, 106), meta, meta_font, MUTED_ON_DARK, 2)

    title = "How a Transformer Reads a Sentence"
    title_font, lines = fit_wrapped(
        draw,
        title,
        CONTENT_W,
        max_lines=2,
        max_size=66,
        min_size=48,
        kind="serif_bold",
    )
    y = 150
    for line in lines:
        draw.text((MARGIN, y), line, font=title_font, fill=WHITE)
        y += title_font.size + 6

    subhead_font = get_font(26, "sans")
    draw.text((MARGIN, y + 12), "One forward pass, token by token.", font=subhead_font, fill=MUTED_ON_DARK)


def _draw_rail(draw: ImageDraw.ImageDraw, travel: float, fade: float) -> None:
    first = _card_center(0)
    last = _card_center(CARD_COUNT - 1)
    pulse_y = first + (last - first) * max(0.0, min(1.0, travel))
    draw.line([(RAIL_X, first), (RAIL_X, last)], fill=LINE_ON_PAPER, width=3)
    if pulse_y > first:
        draw.line([(RAIL_X, first), (RAIL_X, pulse_y)], fill=_mix(LINE_ON_PAPER, ACCENT, fade), width=3)

    for index in range(CARD_COUNT):
        act = _activation(travel, index) * fade
        color = _mix(LINE_ON_PAPER, ACCENT, act)
        width = 3 if act > 0.55 else 2
        draw.line([(RAIL_X, _card_center(index)), (CARD_X, _card_center(index))], fill=color, width=width)


def _draw_pulse(draw: ImageDraw.ImageDraw, travel: float, fade: float) -> None:
    if fade <= 0.02:
        return
    first = _card_center(0)
    last = _card_center(CARD_COUNT - 1)
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


def _draw_card(draw: ImageDraw.ImageDraw, index: int, act: float, stage: Dict[str, str]) -> None:
    top = _card_top(index)
    bottom = top + CARD_H
    fill = _mix(PAPER_SOFT, (232, 238, 252), act)
    border = _mix(LINE_ON_PAPER, ACCENT, act)
    width = 3 if act > 0.5 else 1
    draw.rounded_rectangle([CARD_X, top, CARD_X + CARD_W, bottom], radius=18, fill=fill, outline=border, width=width)

    circle_x = CARD_X + 36
    circle_y = top + CARD_H // 2
    circle_fill = _mix(PAPER, ACCENT, act)
    circle_text = WHITE if act > 0.5 else MUTED_ON_PAPER
    draw.ellipse([circle_x - 22, circle_y - 22, circle_x + 22, circle_y + 22], fill=circle_fill, outline=border)
    number_font = get_font(22, "sans_bold")
    number = str(index + 1)
    number_w = draw.textlength(number, font=number_font)
    draw.text((circle_x - number_w / 2, circle_y - 14), number, font=number_font, fill=circle_text)

    kicker_font = get_font(13, "sans_bold")
    draw_tracked(draw, (CARD_TEXT_X, top + 16), stage["kicker"], kicker_font, _mix(MUTED_ON_PAPER, ACCENT, act), 2)
    title_font = get_font(30, "sans_bold")
    draw.text((CARD_TEXT_X, top + 34), stage["title"], font=title_font, fill=INK)
    detail_font = fit_font(draw, stage["detail"], 596, 19, 15, "sans")
    draw.text((CARD_TEXT_X, top + 72), stage["detail"], font=detail_font, fill=MUTED_ON_PAPER)

    icon = _ICONS.get(stage["icon"])
    if icon:
        icon(draw, ICON_X, circle_y, act)


def _draw_footer(draw: ImageDraw.ImageDraw) -> None:
    draw.line([(MARGIN, 1214), (W - MARGIN, 1214)], fill=LINE_ON_PAPER, width=1)
    draw_tracked(draw, (MARGIN, 1240), "NEUBENCH", get_font(14, "sans_bold"), MUTED_ON_PAPER, 3)
    label = "AI EXPLAINED"
    font = get_font(14, "sans_bold")
    width = _tracked_text_width(draw, label, font, 2)
    draw_tracked(draw, (W - MARGIN - width, 1240), label, font, MUTED_ON_PAPER, 2)


def render_frame(progress: float) -> Image.Image:
    image = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(image)
    _draw_header(draw)
    travel = min(1.0, max(0.0, progress) / 0.82)
    fade = 1.0 if progress <= 0.9 else max(0.0, 1.0 - (progress - 0.9) / 0.1)
    _draw_rail(draw, travel, fade)
    for index, stage in enumerate(STAGES):
        _draw_card(draw, index, _activation(travel, index) * fade, stage)
    _draw_pulse(draw, travel, fade)
    _draw_footer(draw)
    return image


def render_transformer_flow_gif(
    base_name: str = "transformer_flow",
    frames: int = 60,
    duration: int = 80,
) -> Dict[str, Any]:
    folder = OUTPUT_DIR / base_name
    folder.mkdir(parents=True, exist_ok=True)
    images = [render_frame(index / frames) for index in range(frames)]
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
    }
