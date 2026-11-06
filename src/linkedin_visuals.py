"""Premium LinkedIn carousel and handwritten engineering notes renderer.

Produces swipeable PDF carousels and 4:5 hero images from a structured plan.
The design is intentionally handcrafted and editorial:
- Warm archival moleskine paper (cream/ivory) with subtle drafting graph grid
- Classic left drafting margin line (soft red)
- Fountain pen charcoal ink and graphite body text
- Hand-annotated section kickers (// FIELD NOTES)
- Warm canary sticky-notes and parchment callout cards
- Zero neon dark-mode AI slop colors, zero Unicode math bold glyphs.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path("generated_visuals") / "linkedin"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1350
CANVAS_WIDTH, CANVAS_HEIGHT = W, H
MARGIN = 92
CONTENT_W = W - (MARGIN * 2)

# Archival Engineering Notebook & Handwritten Palette
PAPER = (252, 249, 242)          # Warm Ivory Archival Moleskine Paper
PAPER_CARD = (255, 255, 255)     # Clean Drafting Card Fill
PAPER_SOFT = (245, 240, 230)     # Warm Parchment / Secondary Tint
PAPER_STICKY = (254, 249, 228)   # Canary Yellow Sticky-Note Highlight
PAPER_SAGE = (240, 246, 240)     # Soft Sage Box
PAPER_CODE = (247, 245, 238)     # Soft Ivory Code Block Fill
INK = (24, 28, 36)               # Fountain Pen Deep Charcoal Ink
INK_BLUE = (26, 54, 114)         # Parker Royal Blue Fountain Pen Ink
INK_SOFT = (58, 64, 76)          # Graphite Pencil Body Text
MUTED_ON_PAPER = (98, 105, 118)  # Annotations & Metadata Slate
LINE_ON_PAPER = (226, 220, 208)  # Soft Pencil Ruling Lines
GRID_COLOR = (242, 237, 228)     # Drafting Graph Paper Grid
MARGIN_RED = (235, 202, 196)     # Classic Drafting Left Margin Line
ACCENT_TERRACOTTA = (194, 65, 12)# Warm Terracotta / Burnt Sienna Stamp
ACCENT_NAVY = (29, 64, 138)      # Classic Drafting Ink Blue
ACCENT_AMBER = (180, 115, 20)    # Sticky Note Amber Ink
ACCENT_FOREST = (36, 102, 68)    # Sage / Forest Green Ink
ANNOTATION_RED = (185, 42, 32)   # Red Pen Teacher / Margin Annotation

# Soft Highlighters for Authentic Study Notes
HL_YELLOW = (255, 246, 170)      # Pastel Yellow Highlighter
HL_SAGE = (224, 245, 224)        # Pastel Sage Highlighter
HL_CORAL = (255, 228, 222)       # Pastel Coral Highlighter
HL_BLUE = (228, 240, 254)        # Pastel Ice Blue Highlighter

if os.name == "nt":
    _FONT_DIR = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
else:
    _FONT_DIR = Path("/usr/share/fonts")
_FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}


def _font_files(kind: str) -> List[str]:
    if kind == "serif_bold":
        return [
            "georgiab.ttf", "georgia.ttf",
            "DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSerif-Bold.ttf",
        ]
    if kind == "sans_bold":
        return [
            "seguisb.ttf", "segoeuib.ttf", "arialbd.ttf",
            "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        ]
    if kind == "sans":
        return [
            "segoeui.ttf", "arial.ttf",
            "DejaVuSans.ttf", "LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ]
    if kind == "handwriting":
        return [
            "segoepr.ttf", "Inkfree.ttf", "segoeprb.ttf", "comic.ttf",
            "DejaVuSans.ttf", "segoeui.ttf",
        ]
    return [
        "consolab.ttf", "consola.ttf",
        "DejaVuSansMono-Bold.ttf", "LiberationMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono-Bold.ttf",
    ]


def get_font(size: int, kind: str = "sans") -> ImageFont.FreeTypeFont:
    key = (kind, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    for name in _font_files(kind):
        path = Path(name)
        if not path.is_absolute():
            path = _FONT_DIR / name
        try:
            if path.exists():
                loaded = ImageFont.truetype(str(path), size)
                _FONT_CACHE[key] = loaded
                return loaded
        except OSError:
            continue
    try:
        loaded = ImageFont.load_default(size=size)
    except TypeError:
        loaded = ImageFont.load_default()
    _FONT_CACHE[key] = loaded
    return loaded


def _create_notebook_canvas() -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    """Creates a warm engineering notebook page with subtle graph grid and margin rule."""
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # 1. Subtle drafting graph grid (50px spacing)
    for x in range(0, W, 50):
        draw.line([(x, 0), (x, H)], fill=GRID_COLOR, width=1)
    for y in range(0, H, 50):
        draw.line([(0, y), (W, y)], fill=GRID_COLOR, width=1)

    # 2. Classic vertical drafting margin line
    draw.line([(MARGIN - 24, 0), (MARGIN - 24, H)], fill=MARGIN_RED, width=2)

    return img, draw


def _tracked_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, tracking: int) -> int:
    if not text:
        return 0
    return int(sum(draw.textlength(ch, font=font) for ch in text) + tracking * (len(text) - 1))


def draw_tracked(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int],
    tracking: int = 2,
) -> int:
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return int(x)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    words = str(text or "").split()
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_lines: int,
    max_size: int,
    min_size: int,
    kind: str = "sans_bold",
) -> Tuple[ImageFont.FreeTypeFont, List[str]]:
    size = max_size
    while size > min_size:
        font = get_font(size, kind)
        lines = wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
        size -= 4
    font = get_font(min_size, kind)
    return font, wrap_text(draw, text, font, max_width)[:max_lines]


def draw_paragraph(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    xy: Tuple[int, int],
    max_width: int,
    fill: Tuple[int, int, int],
    line_height: int,
    max_lines: int = 14,
) -> int:
    x, y = xy
    paragraphs = str(text or "").split("\n\n")
    total_rendered = 0
    for p_idx, paragraph in enumerate(paragraphs):
        lines = wrap_text(draw, paragraph.replace("\n", " "), font, max_width)
        for line in lines:
            if total_rendered >= max_lines:
                break
            draw.text((x, y), line, font=font, fill=fill)
            y += line_height
            total_rendered += 1
        if p_idx < len(paragraphs) - 1 and total_rendered < max_lines:
            y += int(line_height * 0.45)
    return y


def draw_rule(draw: ImageDraw.ImageDraw, y: int, color: Tuple[int, int, int] = LINE_ON_PAPER, x0: int = MARGIN, x1: int = W - MARGIN) -> None:
    draw.line([(x0, y), (x1, y)], fill=color, width=2)


def draw_footer(draw: ImageDraw.ImageDraw, index: int, total: int) -> None:
    draw_rule(draw, 1238, LINE_ON_PAPER)
    wordmark = get_font(18, "sans_bold")
    draw_tracked(draw, (MARGIN, 1266), "NEUBENCH ARCHITECTURE NOTEBOOK", wordmark, ACCENT_NAVY, tracking=3)
    page = get_font(18, "sans_bold")
    label = f"PAGE {index:02d} / {total:02d}"
    width = int(draw.textlength(label, font=page))
    draw.text((W - MARGIN - width, 1266), label, font=page, fill=MUTED_ON_PAPER)


def _draw_kicker(draw: ImageDraw.ImageDraw, text: str, xy: Tuple[int, int], color: Tuple[int, int, int] = ACCENT_TERRACOTTA) -> None:
    label = re.sub(r"\s+", " ", str(text or "")).strip().upper()[:72]
    if not label:
        return
    font = get_font(20, "sans_bold")
    draw_tracked(draw, xy, label, font, color, tracking=3)


def _draw_margin_note(draw: ImageDraw.ImageDraw, y: int, text: str, color: Tuple[int, int, int] = ANNOTATION_RED) -> None:
    """Draws an authentic handwritten teacher/engineer marginal note near the left margin."""
    clean = str(text or "").strip()
    if not clean:
        return
    font = get_font(18, "handwriting")
    draw.text((MARGIN - 20, y), f"// {clean}", font=font, fill=color)


def _cover_slide(cover: Dict[str, Any], index: int, total: int) -> Image.Image:
    """Cover Slide: Editorial archival monograph on warm graph paper with learning objectives."""
    img, draw = _create_notebook_canvas()

    # Top Notebook Stamp
    draw.rounded_rectangle([MARGIN, 84, MARGIN + 430, 126], radius=6, fill=PAPER_SOFT, outline=LINE_ON_PAPER, width=1)
    stamp_font = get_font(16, "sans_bold")
    draw_tracked(draw, (MARGIN + 16, 94), "// ARCHITECTURAL STUDY NOTES", stamp_font, ACCENT_TERRACOTTA, tracking=2)

    # Category / Kicker
    kicker_text = f"// FIELD REPORT · {cover.get('kicker') or cover.get('category') or 'SYSTEMS DESIGN'}"
    _draw_kicker(draw, kicker_text, (MARGIN, 152), color=ACCENT_NAVY)

    # Double rule below header
    draw_rule(draw, 196, LINE_ON_PAPER)
    draw_rule(draw, 202, LINE_ON_PAPER)

    # Main Headline (Editorial Serif Bold, deep ink)
    headline = str(cover.get("headline") or cover.get("title") or "Engineering Field Notes").strip()
    headline_font, lines = fit_wrapped(draw, headline, CONTENT_W, 3, 76, 52, "serif_bold")
    size = getattr(headline_font, "size", 76)
    y = 236
    for line in lines:
        draw.text((MARGIN, y), line, font=headline_font, fill=INK)
        y += int(size * 1.18)

    # Subhead / Problem framing
    y += 18
    subhead = str(cover.get("subhead") or cover.get("summary") or "").strip()
    if subhead:
        y = draw_paragraph(draw, subhead, get_font(30, "sans"), (MARGIN, y), CONTENT_W, INK_SOFT, 44, max_lines=3)

    # Learning Objectives or Context Card
    objectives = cover.get("objectives") or cover.get("learning_objectives") or []
    if objectives and isinstance(objectives, list):
        card_y = max(y + 24, 660)
        card_y = min(card_y, 760)
        card_h = 360
        draw.rounded_rectangle([MARGIN, card_y, W - MARGIN, card_y + card_h], radius=12, fill=PAPER_CARD, outline=LINE_ON_PAPER, width=2)
        draw.rectangle([MARGIN, card_y, MARGIN + 8, card_y + card_h], fill=ACCENT_NAVY)

        box_tag = get_font(17, "sans_bold")
        draw_tracked(draw, (MARGIN + 28, card_y + 20), "// IN THIS STUDY NOTE · LEARNING OBJECTIVES", box_tag, ACCENT_NAVY, tracking=2)

        obj_y = card_y + 60
        obj_font = get_font(25, "sans")
        for idx, obj in enumerate(objectives[:4], start=1):
            bullet_text = f"{idx}. {obj}"
            obj_y = draw_paragraph(draw, bullet_text, obj_font, (MARGIN + 28, obj_y), CONTENT_W - 56, INK, 36, max_lines=2)
            obj_y += 8
    else:
        # Foundational Context Card
        card_y = max(y + 28, 720)
        card_y = min(card_y, 820)
        card_h = 260
        draw.rounded_rectangle([MARGIN, card_y, W - MARGIN, card_y + card_h], radius=12, fill=PAPER_CARD, outline=LINE_ON_PAPER, width=2)
        draw.rectangle([MARGIN, card_y, MARGIN + 8, card_y + card_h], fill=ACCENT_TERRACOTTA)

        box_tag = get_font(17, "sans_bold")
        draw_tracked(draw, (MARGIN + 28, card_y + 22), "📌 ENGINEERING CONTEXT & PRODUCTION REALITY", box_tag, ACCENT_TERRACOTTA, tracking=2)
        context_desc = str(cover.get("definition") or "Standard patterns look clean in textbook diagrams but hit non-trivial memory, latency, and operational boundaries at scale. These field notes break down the mechanics, trade-offs, and rules of thumb.")
        draw_paragraph(draw, context_desc, get_font(26, "sans"), (MARGIN + 28, card_y + 64), CONTENT_W - 56, INK_SOFT, 38, max_lines=5)

    # Swipe Prompt Bar
    draw_rule(draw, 1140, LINE_ON_PAPER)
    prompt_font = get_font(20, "sans_bold")
    draw_tracked(draw, (MARGIN, 1170), f"SWIPE THROUGH THE {total}-PAGE STUDY NOTES", prompt_font, ACCENT_NAVY, tracking=3)
    arrow = "-->"
    arrow_font = get_font(26, "sans_bold")
    arrow_w = int(draw.textlength(arrow, font=arrow_font))
    draw.text((W - MARGIN - arrow_w, 1164), arrow, font=arrow_font, fill=ACCENT_TERRACOTTA)

    draw_footer(draw, index, total)
    return img


def _point_slide(slide: Dict[str, Any], index: int, total: int) -> Image.Image:
    """Point Slide: Deep technical explanation with warm canary sticky-note callout."""
    img, draw = _create_notebook_canvas()

    # Kicker
    kicker_label = f"// FIELD NOTE {index-1:02d} · {slide.get('kicker') or 'TECHNICAL MECHANICS'}"
    _draw_kicker(draw, kicker_label, (MARGIN, 108), color=ACCENT_TERRACOTTA)
    draw_rule(draw, 146, LINE_ON_PAPER)

    # Title
    title = str(slide.get("title") or "").strip()
    title_font, title_lines = fit_wrapped(draw, title, CONTENT_W, 2, 48, 36, "sans_bold")
    title_size = getattr(title_font, "size", 48)
    y = 176
    for line in title_lines:
        draw.text((MARGIN, y), line, font=title_font, fill=INK)
        y += int(title_size * 1.20)

    # Dynamic placement of teacher margin annotation without overlapping body text
    margin_note = str(slide.get("margin_note") or slide.get("annotation") or "").strip()
    if margin_note:
        y += 10
        m_font = get_font(19, "handwriting")
        m_lines = wrap_text(draw, f"// {margin_note}", m_font, CONTENT_W)
        for ml in m_lines[:2]:
            draw.text((MARGIN, y), ml, font=m_font, fill=ANNOTATION_RED)
            y += 24
        y += 8
    else:
        y += 16

    # Content-aware font and paragraph scaling to support multi-paragraph technical density
    body = str(slide.get("body") or "").strip()
    takeaway = str(slide.get("takeaway") or slide.get("callout") or slide.get("detail") or "").strip()

    if len(body) > 750:
        body_font = get_font(22, "sans")
        line_h = 31
    elif len(body) > 400:
        body_font = get_font(24, "sans")
        line_h = 34
    else:
        body_font = get_font(26, "sans")
        line_h = 37

    # Calculate remaining vertical space for body
    max_body_lines = 18 if takeaway else 22
    y = draw_paragraph(draw, body, body_font, (MARGIN, y), CONTENT_W, INK_SOFT, line_h, max_lines=max_body_lines)

    # Canary Sticky-Note Callout Box (Takeaway / Invariant / So What)
    if takeaway:
        box_top = max(y + 20, 870)
        box_top = min(box_top, 980)
        callout_font = get_font(22, "handwriting")
        callout_lines = wrap_text(draw, takeaway, callout_font, CONTENT_W - 64)
        box_h = min(max(len(callout_lines[:3]) * 32 + 64, 130), 200)

        draw.rounded_rectangle([MARGIN, box_top, W - MARGIN, box_top + box_h], radius=12, fill=PAPER_STICKY, outline=(226, 190, 85), width=2)
        draw.rectangle([MARGIN, box_top, MARGIN + 10, box_top + box_h], fill=ACCENT_AMBER)

        label_font = get_font(18, "sans_bold")
        draw_tracked(draw, (MARGIN + 32, box_top + 18), "// ARCHITECTURAL INVARIANT · SO WHAT", label_font, ACCENT_AMBER, tracking=2)
        draw_paragraph(draw, takeaway, callout_font, (MARGIN + 32, box_top + 52), CONTENT_W - 64, INK, 30, max_lines=3)

    draw_footer(draw, index, total)
    return img

def _comparison_slide(payload: Dict[str, Any], index: int, total: int) -> Image.Image:
    """Comparison / Versus Slide: Side-by-side engineering architectural matrix."""
    img, draw = _create_notebook_canvas()

    # Kicker
    _draw_kicker(draw, f"// COMPARISON MATRIX · {payload.get('kicker') or 'TRADE-OFFS'}", (MARGIN, 108), color=ACCENT_NAVY)
    draw_rule(draw, 146, LINE_ON_PAPER)

    # Title
    title = str(payload.get("title") or "Architectural Comparison Matrix").strip()
    title_font, title_lines = fit_wrapped(draw, title, CONTENT_W, 2, 50, 38, "sans_bold")
    title_size = getattr(title_font, "size", 50)
    y = 182
    for line in title_lines:
        draw.text((MARGIN, y), line, font=title_font, fill=INK)
        y += int(title_size * 1.22)

    # Subhead / intro
    subhead = str(payload.get("intro") or payload.get("subhead") or "").strip()
    if subhead:
        y += 12
        y = draw_paragraph(draw, subhead, get_font(26, "sans"), (MARGIN, y), CONTENT_W, INK_SOFT, 36, max_lines=2)

    # Comparison Table
    table_top = max(y + 24, 380)
    col_w = int((CONTENT_W - 20) / 2)
    col1_x = MARGIN
    col2_x = MARGIN + col_w + 20

    name_a = str(payload.get("name_a") or "Option A")
    name_b = str(payload.get("name_b") or "Option B")

    # Column Headers
    header_h = 58
    draw.rounded_rectangle([col1_x, table_top, col1_x + col_w, table_top + header_h], radius=8, fill=PAPER_SOFT, outline=LINE_ON_PAPER, width=1)
    draw.rounded_rectangle([col2_x, table_top, col2_x + col_w, table_top + header_h], radius=8, fill=PAPER_SOFT, outline=LINE_ON_PAPER, width=1)

    draw.rectangle([col1_x, table_top, col1_x + 6, table_top + header_h], fill=ACCENT_NAVY)
    draw.rectangle([col2_x, table_top, col2_x + 6, table_top + header_h], fill=ACCENT_TERRACOTTA)

    h_font = get_font(22, "sans_bold")
    draw.text((col1_x + 18, table_top + 16), name_a, font=h_font, fill=ACCENT_NAVY)
    draw.text((col2_x + 18, table_top + 16), name_b, font=h_font, fill=ACCENT_TERRACOTTA)

    # Comparison Rows
    rows = payload.get("rows") or payload.get("comparisons") or []
    row_y = table_top + header_h + 16
    row_font = get_font(24, "sans")
    row_label_font = get_font(18, "sans_bold")

    for row in rows[:4]:
        label = str(row.get("attribute") or row.get("label") or "Criterion").strip()
        val_a = str(row.get("val_a") or row.get("option_a") or "").strip()
        val_b = str(row.get("val_b") or row.get("option_b") or "").strip()

        # Attribute tag
        draw.text((col1_x, row_y), f"// {label.upper()}", font=row_label_font, fill=MUTED_ON_PAPER)
        row_y += 26

        # Row cards
        card_h = 92
        draw.rounded_rectangle([col1_x, row_y, col1_x + col_w, row_y + card_h], radius=8, fill=PAPER_CARD, outline=LINE_ON_PAPER, width=1)
        draw.rounded_rectangle([col2_x, row_y, col2_x + col_w, row_y + card_h], radius=8, fill=PAPER_CARD, outline=LINE_ON_PAPER, width=1)

        draw_paragraph(draw, val_a, row_font, (col1_x + 16, row_y + 12), col_w - 32, INK, 32, max_lines=2)
        draw_paragraph(draw, val_b, row_font, (col2_x + 16, row_y + 12), col_w - 32, INK, 32, max_lines=2)
        row_y += card_h + 16

    # Bottom Decision Sticky Note
    takeaway = str(payload.get("takeaway") or payload.get("decision_rule") or "").strip()
    if takeaway:
        sticky_top = max(row_y + 16, 960)
        draw.rounded_rectangle([MARGIN, sticky_top, W - MARGIN, sticky_top + 150], radius=12, fill=PAPER_STICKY, outline=(226, 190, 85), width=2)
        draw.rectangle([MARGIN, sticky_top, MARGIN + 10, sticky_top + 150], fill=ACCENT_AMBER)
        draw_tracked(draw, (MARGIN + 28, sticky_top + 20), "💡 THE SELECTION RULE", get_font(19, "sans_bold"), ACCENT_AMBER, tracking=3)
        draw_paragraph(draw, takeaway, get_font(26, "handwriting"), (MARGIN + 28, sticky_top + 58), CONTENT_W - 56, INK, 36, max_lines=2)

    draw_footer(draw, index, total)
    return img


def _diagram_slide(payload: Dict[str, Any], index: int, total: int) -> Image.Image:
    """Diagram Slide: Clean hand-drawn architectural workflow or data pipeline."""
    img, draw = _create_notebook_canvas()

    # Kicker
    _draw_kicker(draw, f"// ARCHITECTURE DIAGRAM · {payload.get('kicker') or 'DATA FLOW'}", (MARGIN, 108), color=ACCENT_NAVY)
    draw_rule(draw, 146, LINE_ON_PAPER)

    # Title
    title = str(payload.get("title") or "System Architecture & Execution Flow").strip()
    title_font, title_lines = fit_wrapped(draw, title, CONTENT_W, 2, 48, 36, "sans_bold")
    title_size = getattr(title_font, "size", 48)
    y = 176
    for line in title_lines:
        draw.text((MARGIN, y), line, font=title_font, fill=INK)
        y += int(title_size * 1.20)

    # Subtitle if available
    subtitle = str(payload.get("subtitle") or payload.get("subhead") or "").strip()
    if subtitle:
        y += 8
        y = draw_paragraph(draw, subtitle, get_font(22, "sans"), (MARGIN, y), CONTENT_W, INK_SOFT, 29, max_lines=2)

    steps = payload.get("steps") or payload.get("stages") or []
    flow_y = max(y + 24, 320)

    # Render 3 or 4 sequential pipeline cards with connecting arrows
    card_h = 112
    for s_idx, step in enumerate(steps[:4], start=1):
        label = str(step.get("label") or step.get("name") or f"Stage {s_idx}").strip()
        # Support desc, detail, and description keys seamlessly
        detail = str(step.get("desc") or step.get("detail") or step.get("description") or "").strip()

        # Step card
        draw.rounded_rectangle([MARGIN + 48, flow_y, W - MARGIN, flow_y + card_h], radius=10, fill=PAPER_CARD, outline=LINE_ON_PAPER, width=2)
        # Stage badge accent
        draw.rectangle([MARGIN + 48, flow_y, MARGIN + 56, flow_y + card_h], fill=ACCENT_NAVY)

        badge_font = get_font(18, "sans_bold")
        draw.text((MARGIN + 72, flow_y + 14), f"[{s_idx:02d}] {label.upper()}", font=badge_font, fill=ACCENT_NAVY)
        if detail:
            draw_paragraph(draw, detail, get_font(21, "sans"), (MARGIN + 72, flow_y + 44), CONTENT_W - 96, INK_SOFT, 28, max_lines=2)

        # Connector arrow
        if s_idx < min(len(steps), 4):
            arrow_mid_y = flow_y + card_h + 14
            draw.line([(MARGIN + 120, flow_y + card_h), (MARGIN + 120, arrow_mid_y + 10)], fill=ACCENT_TERRACOTTA, width=2)
            draw.line([(MARGIN + 114, arrow_mid_y + 4), (MARGIN + 120, arrow_mid_y + 10)], fill=ACCENT_TERRACOTTA, width=2)
            draw.line([(MARGIN + 126, arrow_mid_y + 4), (MARGIN + 120, arrow_mid_y + 10)], fill=ACCENT_TERRACOTTA, width=2)

        flow_y += card_h + 34

    # Teacher note or latency annotation if present
    annotation = str(payload.get("annotation") or payload.get("note") or "").strip()
    if annotation:
        _draw_margin_note(draw, 1140, annotation)

    draw_footer(draw, index, total)
    return img

def _code_slide(payload: Dict[str, Any], index: int, total: int) -> Image.Image:
    """Code Slide: Clean monospace implementation walkthrough card."""
    img, draw = _create_notebook_canvas()

    # Kicker
    _draw_kicker(draw, f"// CODE IMPLEMENTATION · {payload.get('kicker') or 'CONCRETE EXAMPLE'}", (MARGIN, 108), color=ACCENT_FOREST)
    draw_rule(draw, 146, LINE_ON_PAPER)

    # Title
    title = str(payload.get("title") or "Implementation & Code Mechanics").strip()
    title_font, title_lines = fit_wrapped(draw, title, CONTENT_W, 2, 48, 36, "sans_bold")
    title_size = getattr(title_font, "size", 48)
    y = 176
    for line in title_lines:
        draw.text((MARGIN, y), line, font=title_font, fill=INK)
        y += int(title_size * 1.20)

    # Check for walkthrough/annotation note below code block
    walkthrough = str(payload.get("annotation") or payload.get("walkthrough") or payload.get("body") or "").strip()

    # Code Block Card
    code_top = max(y + 20, 310)
    code_text = str(payload.get("code") or payload.get("snippet") or "").strip()
    code_lines = code_text.splitlines()
    total_lines = len(code_lines)

    # Content-aware font and line-height scaling so code is never truncated
    if total_lines > 16:
        mono_font = get_font(17, "mono")
        line_num_font = get_font(16, "sans")
        line_h = 26
    elif total_lines > 12:
        mono_font = get_font(19, "mono")
        line_num_font = get_font(17, "sans")
        line_h = 32
    else:
        mono_font = get_font(21, "mono")
        line_num_font = get_font(18, "sans")
        line_h = 36

    max_block_h = 780 if not walkthrough else 670
    visible_lines = code_lines[:min(total_lines, 24)]
    block_h = min(max(len(visible_lines) * line_h + 58, 260), max_block_h)

    draw.rounded_rectangle([MARGIN, code_top, W - MARGIN, code_top + block_h], radius=12, fill=PAPER_CODE, outline=LINE_ON_PAPER, width=2)
    draw.rounded_rectangle([MARGIN, code_top, W - MARGIN, code_top + 38], radius=12, fill=PAPER_SOFT)
    draw.rectangle([MARGIN, code_top + 26, W - MARGIN, code_top + 38], fill=PAPER_SOFT)
    lang_label = str(payload.get("language") or "PYTHON / ARCHITECTURE").upper()
    draw_tracked(draw, (MARGIN + 24, code_top + 10), f"// {lang_label}", get_font(15, "sans_bold"), ACCENT_NAVY, tracking=2)

    code_y = code_top + 48
    for l_idx, line in enumerate(visible_lines, start=1):
        draw.text((MARGIN + 18, code_y), f"{l_idx:02d}", font=line_num_font, fill=MUTED_ON_PAPER)
        draw.text((MARGIN + 58, code_y), line, font=mono_font, fill=INK)
        code_y += line_h

    # Explanation or annotation of code mechanics below
    if walkthrough:
        note_top = code_top + block_h + 20
        note_h = min(max(110, 1200 - note_top), 170)
        draw.rounded_rectangle([MARGIN, note_top, W - MARGIN, note_top + note_h], radius=12, fill=PAPER_STICKY, outline=(226, 190, 85), width=2)
        draw.rectangle([MARGIN, note_top, MARGIN + 10, note_top + note_h], fill=ACCENT_AMBER)
        draw_tracked(draw, (MARGIN + 28, note_top + 16), "// IMPLEMENTATION INVARIANT", get_font(17, "sans_bold"), ACCENT_AMBER, tracking=2)
        draw_paragraph(draw, walkthrough, get_font(21, "handwriting"), (MARGIN + 28, note_top + 48), CONTENT_W - 56, INK, 29, max_lines=3)

    draw_footer(draw, index, total)
    return img

def _pitfalls_slide(payload: Dict[str, Any], index: int, total: int) -> Image.Image:
    """Pitfalls & Failure Modes Slide: Production mistakes, impacts, and preventions."""
    img, draw = _create_notebook_canvas()

    # Kicker
    _draw_kicker(draw, f"// PRODUCTION FAILURE MODES · {payload.get('kicker') or 'COMMON TRAPS'}", (MARGIN, 108), color=ANNOTATION_RED)
    draw_rule(draw, 146, LINE_ON_PAPER)

    # Title
    title = str(payload.get("title") or "Common Production Pitfalls & Edge Cases").strip()
    title_font, title_lines = fit_wrapped(draw, title, CONTENT_W, 2, 48, 36, "sans_bold")
    title_size = getattr(title_font, "size", 48)
    y = 176
    for line in title_lines:
        draw.text((MARGIN, y), line, font=title_font, fill=INK)
        y += int(title_size * 1.20)

    # Support aliases: traps, pitfalls, mistakes
    pitfalls = payload.get("traps") or payload.get("pitfalls") or payload.get("mistakes") or []
    y = max(y + 24, 300)

    for p_idx, pit in enumerate(pitfalls[:3], start=1):
        trap_title = str(pit.get("trap") or pit.get("mistake") or pit.get("title") or f"Pitfall {p_idx}").strip()
        impact = str(pit.get("impact") or "").strip()
        prevention = str(pit.get("prevention") or pit.get("fix") or "").strip()

        card_h = 186 if impact else 136
        draw.rounded_rectangle([MARGIN, y, W - MARGIN, y + card_h], radius=10, fill=PAPER_CARD, outline=LINE_ON_PAPER, width=2)
        draw.rectangle([MARGIN, y, MARGIN + 8, y + card_h], fill=ANNOTATION_RED)

        draw_tracked(draw, (MARGIN + 24, y + 14), f"[!] {p_idx}. {trap_title.upper()}", get_font(18, "sans_bold"), ANNOTATION_RED, tracking=2)

        content_y = y + 44
        if impact:
            imp_text = f"Impact: {impact}"
            content_y = draw_paragraph(draw, imp_text, get_font(21, "sans"), (MARGIN + 24, content_y), CONTENT_W - 48, MUTED_ON_PAPER, 27, max_lines=2)
            content_y += 6

        if prevention:
            prev_text = f"Fix: {prevention}"
            draw_paragraph(draw, prev_text, get_font(22, "sans_bold"), (MARGIN + 24, content_y), CONTENT_W - 48, INK, 28, max_lines=2)

        y += card_h + 16

    _draw_margin_note(draw, 1140, "Rule: Benchmark under production concurrency before shipping!")
    draw_footer(draw, index, total)
    return img

def _framework_slide(framework: Dict[str, Any], index: int, total: int) -> Image.Image:
    """Framework Slide: Step-by-step 2026 playbook with hand-ruled number circles."""
    img, draw = _create_notebook_canvas()

    # Kicker
    _draw_kicker(draw, f"// THE 2026 PRODUCTION PLAYBOOK · {framework.get('kicker') or 'CHECKLIST'}", (MARGIN, 108), color=ACCENT_NAVY)
    draw_rule(draw, 146, LINE_ON_PAPER)

    # Title
    title = str(framework.get("title") or "Battle-tested Rules for Engineering Teams").strip()
    title_font, title_lines = fit_wrapped(draw, title, CONTENT_W, 2, 54, 40, "sans_bold")
    title_size = getattr(title_font, "size", 54)
    y = 182
    for line in title_lines:
        draw.text((MARGIN, y), line, font=title_font, fill=INK)
        y += int(title_size * 1.22)

    steps = [step for step in (framework.get("steps") or []) if isinstance(step, dict)][:4]
    y = max(y + 40, 420)
    circle_x = MARGIN + 32
    line_x = circle_x

    # Dashed vertical timeline connector
    if len(steps) > 1:
        dash_y = y + 36
        end_y = y + (len(steps) - 1) * 168 + 36
        while dash_y < end_y:
            draw.line([(line_x, dash_y), (line_x, min(dash_y + 12, end_y))], fill=ACCENT_NAVY, width=2)
            dash_y += 20

    for position, step in enumerate(steps, start=1):
        # Step Number Badge
        draw.ellipse([circle_x - 26, y, circle_x + 26, y + 52], fill=ACCENT_NAVY)
        number_font = get_font(23, "sans_bold")
        number = f"{position:02d}"
        number_w = int(draw.textlength(number, font=number_font))
        draw.text((circle_x - number_w / 2, y + 12), number, font=number_font, fill=(255, 255, 255))

        label = str(step.get("label") or "").strip()
        detail = str(step.get("detail") or "").strip()

        # Step card
        draw.rounded_rectangle([circle_x + 50, y - 8, W - MARGIN, y + 124], radius=10, fill=PAPER_CARD, outline=LINE_ON_PAPER, width=1)
        draw_paragraph(draw, label, get_font(27, "sans_bold"), (circle_x + 72, y + 10), CONTENT_W - 120, INK, 34, max_lines=1)
        draw_paragraph(draw, detail, get_font(24, "sans"), (circle_x + 72, y + 48), CONTENT_W - 120, INK_SOFT, 32, max_lines=2)
        y += 168

    draw_footer(draw, index, total)
    return img


def _cta_slide(cta: Dict[str, Any], index: int, total: int) -> Image.Image:
    """CTA / Summary Slide: Golden Rule on sticky-note + Revision bullets + discussion invitation."""
    cta = cta or {}
    img, draw = _create_notebook_canvas()

    # Kicker
    _draw_kicker(draw, f"// SUMMARY & THE GOLDEN RULE · {cta.get('kicker') or 'FIELD NOTES'}", (MARGIN, 108), color=ACCENT_TERRACOTTA)
    draw_rule(draw, 146, LINE_ON_PAPER)

    # Large Canary Yellow Sticky Note Card (Golden Rule of Thumb)
    card_top = 180
    card_h = 240
    draw.rounded_rectangle([MARGIN, card_top, W - MARGIN, card_top + card_h], radius=16, fill=PAPER_STICKY, outline=(226, 190, 85), width=3)
    draw.rectangle([MARGIN, card_top, MARGIN + 14, card_top + card_h], fill=ACCENT_AMBER)

    draw_tracked(draw, (MARGIN + 36, card_top + 22), "// THE GOLDEN RULE OF THUMB", get_font(20, "sans_bold"), ACCENT_AMBER, tracking=2)

    # Support golden_rule and headline
    headline = str(cta.get("golden_rule") or cta.get("headline") or "Choose the right tool for the engineering requirements.").strip()
    headline_font, headline_lines = fit_wrapped(draw, headline, CONTENT_W - 72, 3, 38, 28, "handwriting")
    h_size = getattr(headline_font, "size", 38)
    hy = card_top + 64
    for line in headline_lines:
        draw.text((MARGIN + 36, hy), line, font=headline_font, fill=INK)
        hy += int(h_size * 1.25)

    # Support checklist and revision_points
    summary_items = cta.get("checklist") or cta.get("revision_points") or cta.get("summary_bullets") or []
    next_top = card_top + card_h + 20

    if summary_items and isinstance(summary_items, list):
        rev_h = 290
        draw.rounded_rectangle([MARGIN, next_top, W - MARGIN, next_top + rev_h], radius=14, fill=PAPER_CARD, outline=LINE_ON_PAPER, width=2)
        draw_tracked(draw, (MARGIN + 32, next_top + 22), "// QUICK REVISION CHECKLIST", get_font(19, "sans_bold"), ACCENT_NAVY, tracking=2)
        b_y = next_top + 58
        for idx, bullet in enumerate(summary_items[:3], start=1):
            b_text = f"•  {bullet}"
            b_y = draw_paragraph(draw, b_text, get_font(22, "sans"), (MARGIN + 32, b_y), CONTENT_W - 64, INK, 30, max_lines=2)
            b_y += 6
        next_top += rev_h + 18

    # Discussion & Action Card
    disc_prompt = str(cta.get("discussion_prompt") or cta.get("prompt") or "").strip()
    if not disc_prompt:
        disc_prompt = "What failure mode have you encountered when running this architecture in production?"

    disc_h = min(max(180, 1200 - next_top), 220)
    draw.rounded_rectangle([MARGIN, next_top, W - MARGIN, next_top + disc_h], radius=14, fill=PAPER_SOFT, outline=LINE_ON_PAPER, width=1)
    draw_tracked(draw, (MARGIN + 28, next_top + 20), "// ENGINEERING DISCUSSION", get_font(18, "sans_bold"), ACCENT_TERRACOTTA, tracking=2)
    draw_paragraph(draw, disc_prompt, get_font(21, "sans"), (MARGIN + 28, next_top + 54), CONTENT_W - 56, INK, 28, max_lines=2)

    site = str(cta.get("website") or "app.neubench.workers.dev").strip()
    if site:
        pill_font = get_font(16, "sans_bold")
        pill_w = int(draw.textlength(site, font=pill_font)) + 32
        draw.rounded_rectangle([MARGIN + 28, next_top + disc_h - 52, MARGIN + 28 + pill_w, next_top + disc_h - 14], radius=8, fill=PAPER_CARD, outline=LINE_ON_PAPER, width=1)
        draw.text((MARGIN + 44, next_top + disc_h - 42), site, font=pill_font, fill=ACCENT_NAVY)

    draw_footer(draw, index, total)
    return img

def build_slides(plan: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """Builds a dynamic list of slides from either modern 'pages' schema or legacy schema."""
    if plan.get("pages") and isinstance(plan["pages"], list):
        slides = []
        for p in plan["pages"]:
            if isinstance(p, dict):
                kind = p.get("type") or p.get("kind") or "concept"
                slides.append((kind, p))
        if slides:
            return slides

    # Legacy schema fallback
    slides: List[Tuple[str, Dict[str, Any]]] = [("cover", plan.get("cover") or {})]
    for point in (plan.get("slides") or plan.get("points") or [])[:5]:
        if isinstance(point, dict):
            slides.append((point.get("type", "point"), point))
    framework = plan.get("framework")
    if isinstance(framework, dict) and framework.get("steps"):
        slides.append(("framework", framework))
    slides.append(("cta", plan.get("cta") or {}))
    return slides


def _slug(value: str, fallback: str = "carousel") -> str:
    raw = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return (raw[:96] or fallback)


def _render_slide(kind: str, payload: Dict[str, Any], index: int, total: int) -> Image.Image:
    if kind == "cover":
        return _cover_slide(payload, index, total)
    if kind in ("comparison", "versus"):
        return _comparison_slide(payload, index, total)
    if kind in ("diagram", "flowchart", "architecture"):
        return _diagram_slide(payload, index, total)
    if kind in ("code", "syntax", "implementation"):
        return _code_slide(payload, index, total)
    if kind in ("pitfalls", "mistakes", "edge_cases"):
        return _pitfalls_slide(payload, index, total)
    if kind in ("framework", "playbook", "process"):
        return _framework_slide(payload, index, total)
    if kind in ("cta", "summary", "golden_rule"):
        return _cta_slide(payload, index, total)
    return _point_slide(payload, index, total)


def render_linkedin_carousel(plan: Dict[str, Any], base_name: Optional[str] = None) -> Dict[str, Any]:
    """Renders a multi-page PDF carousel plus preview PNGs. Returns asset paths."""
    seed = str(plan.get("cover", {}).get("headline") or plan.get("topic") or "linkedin")
    digest = hashlib.md5(seed.encode("utf-8")).hexdigest()[:8]
    base = f"{_slug(seed)}_{digest}" if not base_name else _slug(base_name)
    folder = OUTPUT_DIR / base
    folder.mkdir(parents=True, exist_ok=True)

    specs = build_slides(plan)
    total = len(specs)
    images: List[Image.Image] = []
    png_paths: List[str] = []
    for index, (kind, payload) in enumerate(specs, start=1):
        image = _render_slide(kind, payload, index, total)
        images.append(image)
        png_path = folder / f"slide_{index:02d}.png"
        image.save(png_path, "PNG")
        png_paths.append(str(png_path))

    pdf_path = folder / f"{base}.pdf"
    images[0].save(
        pdf_path,
        "PDF",
        resolution=144.0,
        save_all=True,
        append_images=images[1:],
    )

    return {
        "base": base,
        "folder": str(folder),
        "pdf_path": str(pdf_path),
        "png_paths": png_paths,
        "slide_paths": png_paths,
        "slide_count": total,
        "alt_text": str(plan.get("alt_text") or "").strip(),
    }


def render_linkedin_hero(plan: Dict[str, Any], base_name: Optional[str] = None) -> str:
    """Renders a single 4:5 hero image (cover layout) for image-only posts."""
    seed = str(plan.get("cover", {}).get("headline") or plan.get("topic") or "linkedin")
    digest = hashlib.md5((seed + "_hero").encode("utf-8")).hexdigest()[:8]
    base = f"{_slug(seed)}_{digest}" if not base_name else _slug(base_name)
    folder = OUTPUT_DIR / base
    folder.mkdir(parents=True, exist_ok=True)
    image = _cover_slide(plan.get("cover") or {}, 1, 1)
    path = folder / f"{base}_hero.png"
    image.save(path, "PNG")
    return str(path)
