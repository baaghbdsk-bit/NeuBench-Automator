"""Pro LinkedIn Visuals Engine (Playwright HTML/CSS/SVG -> 1080x1350 PNG & Multi-Slide PDF Carousel).

Features:
- 4 Topic-Adaptive Editorial Themes (arch_blueprint, editorial_paper, comparison_split, builder_notes)
- Bespoke topic-specific inline SVG diagrams driven by the actual article
- Smart typographic fallback (extracts real article sentences; zero generic 3-box diagrams)
- Varied 5-slide PDF carousel layouts (Cover -> Problem/Split -> Custom SVG -> Breakdown -> Author CTA)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

import config

OUTPUT_DIR = Path("generated_visuals") / "linkedin"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1350

THEMES = {
    "arch_blueprint": {
        "bg": "#F4F8FF",
        "grid": "rgba(37, 99, 235, 0.06)",
        "kicker_bg": "#DBEAFE",
        "kicker_border": "#93C5FD",
        "kicker_text": "#1E40AF",
        "card_border": "#BFDBFE",
        "accent_a": "#0284C7",
        "accent_b": "#059669",
    },
    "editorial_paper": {
        "bg": "#FAF9F6",
        "grid": "rgba(15, 23, 42, 0.04)",
        "kicker_bg": "#FEF3C7",
        "kicker_border": "#FCD34D",
        "kicker_text": "#92400E",
        "card_border": "#E5E7EB",
        "accent_a": "#C2410C",
        "accent_b": "#0F766E",
    },
    "comparison_split": {
        "bg": "#FFFFFF",
        "grid": "rgba(15, 23, 42, 0.03)",
        "kicker_bg": "#F1F5F9",
        "kicker_border": "#0F172A",
        "kicker_text": "#0F172A",
        "card_border": "#0F172A",
        "accent_a": "#059669",
        "accent_b": "#E11D48",
    },
    "builder_notes": {
        "bg": "#F7FAF8",
        "grid": "rgba(5, 150, 105, 0.05)",
        "kicker_bg": "#D1FAE5",
        "kicker_border": "#6EE7B7",
        "kicker_text": "#065F46",
        "card_border": "#A7F3D0",
        "accent_a": "#059669",
        "accent_b": "#0284C7",
    },
}


def _sanitize_svg(raw_svg: str) -> str:
    if not raw_svg or "<svg" not in raw_svg.lower():
        return ""
    cleaned = re.sub(r"<script[\s\S]*?</script>", "", raw_svg, flags=re.IGNORECASE)
    cleaned = re.sub(r"\son\w+\s*=\s*(['\"]).*?\1", "", cleaned, flags=re.IGNORECASE)
    m = re.search(r"<svg[\s\S]*?</svg>", cleaned, flags=re.IGNORECASE)
    if not m:
        return ""
    svg = m.group(0)
    if "viewBox" not in svg:
        svg = svg.replace("<svg", '<svg viewBox="0 0 920 440"', 1)
    svg = re.sub(
        r"<svg([^>]*)>",
        lambda g: "<svg"
        + re.sub(r'\s(width|height)\s*=\s*["\'][^"\']*["\']', "", g.group(1))
        + ' class="w-full h-auto max-h-[500px]">',
        svg,
        count=1,
    )
    return svg


def _pick_fallback_theme(topic: str) -> str:
    low = topic.lower()
    if any(k in low for k in (" vs ", "versus", "compare", "better than")):
        return "comparison_split"
    if any(k in low for k in ("architecture", "database", "rag", "moe", "gpu", "cpu", "cache", "network", "kernel")):
        return "arch_blueprint"
    if any(k in low for k in ("how to", "guide", "benchmark", "speed", "optimize", "tips")):
        return "builder_notes"
    return "editorial_paper"


def _call_gemini_json(prompt: str) -> Optional[Dict[str, Any]]:
    api_key = getattr(config, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    model_name = getattr(config, "GEMINI_MODEL", "gemini-3.5-flash") or "gemini-3.5-flash"
    if not api_key:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        candidates = []
        for m_name in (model_name, "gemini-3.5-flash-lite", "gemini-2.5-flash"):
            if m_name and m_name not in candidates:
                candidates.append(m_name)
        for m_name in candidates:
            try:
                resp = client.models.generate_content(model=m_name, contents=prompt)
                raw = resp.text or ""
                m = re.search(r"\{[\s\S]*\}", raw)
                if m:
                    return json.loads(m.group(0))
            except Exception as exc:
                print(f"[linkedin_pro_visuals] Gemini {m_name} failed: {exc}")
    except Exception as exc:
        print(f"[linkedin_pro_visuals] Gemini init error: {exc}")
    return None


def _extract_article_points(summary: str, article_text: str) -> List[str]:
    source = (article_text or summary or "").strip()
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", source) if len(s.strip()) > 25]
    return sents[:4] if sents else [summary or "Core engineering breakdown."]


def _build_visual_spec(topic: str, summary: str, article_text: str, qa_feedback: str = "") -> Dict[str, Any]:
    feedback_block = (
        f"\nPREVIOUS RENDER FAILED VISUAL QA — FIX THESE SPECIFIC ISSUES:\n{qa_feedback}\n"
        if qa_feedback
        else ""
    )
    prompt = f"""You are a senior staff engineer & editorial designer (ByteByteGo / Stripe Docs / Apple Keynote).
Design a crystal-clear, topic-unique Light-Mode LinkedIn visual attachment for this exact post:

Topic: {topic}
Summary: {summary}
Article Excerpt: {article_text[:1200]}
{feedback_block}

STRICT RULES:
- Pick the best `theme` for this topic:
  - "arch_blueprint" (Systems, databases, ML internals, networking)
  - "editorial_paper" (AI news, industry shifts, company updates, policy)
  - "comparison_split" (A vs B comparisons, benchmarks, myth-busting)
  - "builder_notes" (Workflows, tutorials, engineering checklists)
- ZERO generic boilerplate ("Payload Dispatch", "State Evaluation", "Downstream Commit", "Strict bounded memory pool").
- Every label, node, and metric MUST be 100% specific to "{topic}".
- Write a crisp inline `<svg viewBox="0 0 920 440">` diagram on a clean light background (`#F8FAFC` / `#FFFFFF`), dark slate ink (`#0F172A`), and sharp accents (`#0284C7` blue, `#059669` emerald, `#E11D48` rose, `#D97706` amber). Minimum `font-size="20"` inside SVG so text is never tiny or truncated.
- Return ONLY valid JSON:
{{
  "theme": "arch_blueprint" | "editorial_paper" | "comparison_split" | "builder_notes",
  "kicker": "SHORT CATEGORY TAG",
  "headline": "Sharp 4-8 word title",
  "subtitle": "One concrete sentence explaining the core mechanism.",
  "diagram_title": "1. HOW IT ACTUALLY WORKS",
  "svg": "<svg viewBox='0 0 920 440'>...</svg>",
  "takeaways": [
    {{"tag": "01 // MECHANISM", "title": "Short title", "body": "Concrete 1-sentence insight from the article."}},
    {{"tag": "02 // TRADEOFF", "title": "Short title", "body": "Concrete 1-sentence tradeoff or failure mode."}}
  ],
  "slides": [
    {{"layout": "cover", "eyebrow": "01 // FIELD NOTES", "title": "Bold cover headline", "body": "Why this matters right now."}},
    {{"layout": "split", "eyebrow": "02 // THE SHIFT", "left_title": "OLD WAY", "left_body": "Limitation", "right_title": "NEW WAY", "right_body": "Breakthrough"}},
    {{"layout": "diagram", "eyebrow": "03 // ARCHITECTURE", "title": "How it works"}},
    {{"layout": "points", "eyebrow": "04 // PRODUCTION REALITY", "title": "Key tradeoffs", "points": ["Point 1", "Point 2", "Point 3"]}},
    {{"layout": "cta", "eyebrow": "05 // TAKEAWAY", "title": "What to do next", "body": "One actionable rule for builders."}}
  ]
}}"""
    parsed = _call_gemini_json(prompt)
    if parsed and isinstance(parsed.get("takeaways"), list) and _sanitize_svg(str(parsed.get("svg") or "")):
        return parsed

    # Smart typographic fallback (extracts real article sentences—zero generic 3-box diagrams)
    points = _extract_article_points(summary, article_text)
    return {
        "theme": _pick_fallback_theme(topic),
        "kicker": "ENGINEERING BREAKDOWN",
        "headline": topic[:68],
        "subtitle": points[0][:145] if points else summary[:145],
        "diagram_title": "KEY INSIGHTS",
        "svg": "",
        "takeaways": [
            {"tag": "01 // CORE SIGNAL", "title": "What Changed", "body": points[1][:150] if len(points) > 1 else (summary[:150] or topic)},
            {"tag": "02 // BUILDER NOTE", "title": "Practical Impact", "body": points[2][:150] if len(points) > 2 else "Validate latency, cost, and accuracy on your own workload."},
        ],
        "slides": [
            {"layout": "cover", "eyebrow": "01 // OVERVIEW", "title": topic[:58], "body": points[0][:150] if points else summary[:150]},
            {"layout": "points", "eyebrow": "02 // BREAKDOWN", "title": "Key Takeaways", "points": points[:3]},
            {"layout": "cta", "eyebrow": "03 // NEXT STEP", "title": "Bottom Line", "body": points[-1][:160] if points else topic},
        ],
    }


_AUTO_FIT_SVG_JS = """
() => {
  document.querySelectorAll('svg').forEach(svg => {
    const vb = svg.viewBox && svg.viewBox.baseVal ? svg.viewBox.baseVal : { x: 0, y: 0, width: 920, height: 440 };
    const rects = Array.from(svg.querySelectorAll('rect')).map(r => {
      const b = r.getBBox();
      return { x: b.x, y: b.y, w: b.width, h: b.height, area: b.width * b.height };
    }).filter(r => r.w > 30 && r.h > 18 && r.w < vb.width * 0.92);

    svg.querySelectorAll('text').forEach(txt => {
      const tb = txt.getBBox();
      if (!tb || tb.width <= 0) return;
      const cx = tb.x + tb.width / 2;
      const cy = tb.y + tb.height / 2;
      // Find smallest rect containing the text center
      const containers = rects.filter(r => cx >= r.x && cx <= r.x + r.w && cy >= r.y && cy <= r.y + r.h)
                              .sort((a, b) => a.area - b.area);
      const box = containers[0] || { x: vb.x + 16, y: vb.y + 16, w: vb.width - 32, h: vb.height - 32 };
      const maxW = Math.max(40, box.w - 24);
      if (tb.width > maxW) {
        const cs = window.getComputedStyle(txt);
        const curFs = parseFloat(txt.getAttribute('font-size') || cs.fontSize || '18') || 18;
        const newFs = Math.max(11, curFs * (maxW / tb.width) * 0.96);
        txt.setAttribute('font-size', newFs.toFixed(1));
        txt.style.fontSize = newFs.toFixed(1) + 'px';
      }
      // Re-check horizontal bounds and nudge if needed
      const nb = txt.getBBox();
      if (nb.x < box.x + 10) {
        const shift = (box.x + 10) - nb.x;
        const oldX = parseFloat(txt.getAttribute('x') || '0');
        if (!isNaN(oldX)) txt.setAttribute('x', (oldX + shift).toFixed(1));
      } else if (nb.x + nb.width > box.x + box.w - 10) {
        const shift = (nb.x + nb.width) - (box.x + box.w - 10);
        const oldX = parseFloat(txt.getAttribute('x') || '0');
        if (!isNaN(oldX)) txt.setAttribute('x', (oldX - shift).toFixed(1));
      }
    });
  });
}
"""


def _render_html_to_png(html_str: str, out_png: Path) -> None:
    from playwright.sync_api import sync_playwright
    tmp_html = out_png.with_suffix(".html")
    tmp_html.write_text(html_str, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(tmp_html.resolve().as_uri(), wait_until="networkidle")
        page.wait_for_timeout(350)
        page.evaluate(_AUTO_FIT_SVG_JS)
        page.wait_for_timeout(50)
        page.screenshot(path=str(out_png), type="png")
        browser.close()


def _log_li_feedback(topic: str, png_path: Path, score: int, passed: bool, defects: List[str], summary: str) -> None:
    log_path = Path.home() / ".gemini" / "config" / "skills" / "creative-production-director" / "feedback-log.jsonl"
    if not log_path.parent.exists():
        return
    try:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "media_type": "image",
            "model_provider": "linkedin_pro_visuals + gemini-3.5-flash-qa",
            "settings": "1080x1350",
            "prompt": topic,
            "output_path": str(png_path),
            "score": score,
            "passed": passed,
            "critical_defects": defects,
            "revisions": summary,
            "final_result": "accepted" if passed else "rejected",
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _verify_png_with_gemini(topic: str, png_path: Path) -> Dict[str, Any]:
    """Inspect rendered 1080x1350 PNG against the 80/100 Image Quality Rubric via Gemini Vision."""
    api_key = getattr(config, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    if not api_key or not png_path.exists():
        return {"passed": True, "skipped": "no_api_key_or_file"}
    try:
        from google import genai
        from google.genai import types
    except Exception as exc:
        return {"passed": True, "skipped": f"google-genai unavailable: {exc}"}

    rubric = (
        "You are a strict Image Quality Auditor. Inspect this 1080x1350 Light-Mode LinkedIn technical graphic. "
        "Score out of 100 (Composition 15, Lighting/Contrast 15, Realism/Clarity 20, Subject/Diagram Quality 20, "
        "Detail Quality 10, Aesthetic Appeal 10, Mobile Platform Suitability 10). "
        "List any CRITICAL DEFECTS (text overflowing boxes, clipped/cut-off labels, overlapping SVG nodes/arrows, "
        "unreadable tiny text, or blank diagram area). "
        'Respond ONLY with JSON: {"score": <int 0-100>, "critical_defects": [<strings>], "summary": "<1-line>"}'
    )
    img_part = types.Part.from_bytes(data=png_path.read_bytes(), mime_type="image/png")
    client = genai.Client(api_key=api_key)
    for model_name in ("gemini-3.5-flash", "gemini-3.5-flash-lite"):
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=[rubric, img_part],
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            parsed = json.loads(resp.text or "{}")
            score = int(parsed.get("score", 0))
            defects = [str(d) for d in (parsed.get("critical_defects") or []) if str(d).strip()]
            summary = str(parsed.get("summary") or "")
            passed = score >= 80 and not defects
            _log_li_feedback(topic, png_path, score, passed, defects, summary)
            return {"score": score, "passed": passed, "critical_defects": defects, "summary": summary, "model": model_name}
        except Exception:
            continue
    return {"passed": True, "skipped": "vision_qa_unavailable"}


def render_pro_architecture_png(topic: str, summary: str = "", article_text: str = "") -> Dict[str, Any]:
    """Render a crisp 1080x1350 topic-themed Light-Mode editorial PNG via Playwright, with 80/100 Visual QA + 1 retry."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic.lower()).strip("_")[:32] or "post"
    digest = hashlib.md5(topic.encode("utf-8")).hexdigest()[:8]
    out_dir = OUTPUT_DIR / f"pro_{slug}_{digest}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_png = out_dir / f"{slug}.png"
    creator = getattr(config, "CREATOR_NAME", "Vishnu")

    qa_feedback = ""
    spec: Dict[str, Any] = {}
    theme_key = _pick_fallback_theme(topic)
    qa_result: Dict[str, Any] = {}

    for attempt in range(1, 3):
        spec = _build_visual_spec(topic, summary, article_text, qa_feedback=qa_feedback)
        theme_key = str(spec.get("theme") or _pick_fallback_theme(topic))
        th = THEMES.get(theme_key, THEMES["editorial_paper"])
        svg_html = _sanitize_svg(str(spec.get("svg") or ""))

        takeaways = (spec.get("takeaways") or [])[:2]
        cards_html = ""
        if theme_key == "comparison_split" and len(takeaways) == 2:
            cols = ""
            for idx, item in enumerate(takeaways):
                top_col = th["accent_a"] if idx == 0 else th["accent_b"]
                clean_tag = str(item.get("tag", "")).replace("//", "·").strip()
                cols += f"""
        <div style="border-color:{th['card_border']}; border-top-width:8px; border-top-color:{top_col};" class="bg-white border-2 rounded-2xl p-6 shadow-sm space-y-2 flex flex-col justify-between">
          <div style="color:{top_col};" class="text-sm font-bold">{clean_tag}</div>
          <div class="text-2xl font-extrabold text-slate-900 leading-tight">{item.get('title', '')}</div>
          <p class="text-lg text-slate-600 leading-snug font-medium">{item.get('body', '')}</p>
        </div>"""
            cards_container = f'<div class="grid grid-cols-2 gap-4">{cols}</div>'
        elif theme_key == "builder_notes":
            for idx, item in enumerate(takeaways):
                badge_col = th["accent_a"] if idx == 0 else th["accent_b"]
                clean_tag = str(item.get("tag", "")).replace("//", "·").strip()
                cards_html += f"""
        <div style="border-color:{th['card_border']};" class="bg-white border-2 rounded-2xl p-6 shadow-sm flex items-start gap-4">
          <div style="background:{badge_col};" class="w-10 h-10 rounded-xl text-white font-mono text-lg font-extrabold flex items-center justify-center shrink-0">0{idx + 1}</div>
          <div class="space-y-1">
            <div style="color:{badge_col};" class="text-xs font-bold">{clean_tag}</div>
            <div class="text-2xl font-extrabold text-slate-900">{item.get('title', '')}</div>
            <p class="text-xl text-slate-600 leading-snug font-medium">{item.get('body', '')}</p>
          </div>
        </div>"""
            cards_container = f'<div class="space-y-4">{cards_html}</div>'
        else:
            for idx, item in enumerate(takeaways):
                border_col = th["accent_a"] if idx == 0 else th["accent_b"]
                clean_tag = str(item.get("tag", "")).replace("//", "·").strip()
                cards_html += f"""
        <div style="border-color:{th['card_border']}; border-left-width:8px; border-left-color:{border_col};" class="bg-white border-2 rounded-2xl p-6 shadow-sm space-y-1.5">
          <div style="color:{border_col};" class="text-sm font-bold">{clean_tag}</div>
          <div class="text-2xl font-extrabold text-slate-900">{item.get('title', '')}</div>
          <p class="text-xl text-slate-600 leading-snug font-medium">{item.get('body', '')}</p>
        </div>"""
            cards_container = f'<div class="space-y-4">{cards_html}</div>'

        if svg_html:
            center_section = f"""
        <div style="border-color:{th['card_border']};" class="bg-white border-2 rounded-3xl p-6 shadow-md space-y-3 my-3">
          <div class="text-base font-bold text-slate-600 border-b border-slate-100 pb-2">
            {spec.get('diagram_title', '1. Architecture')}
          </div>
          <div class="rounded-2xl bg-slate-50 border border-slate-200 p-3 flex items-center justify-center">
            {svg_html}
          </div>
        </div>"""
        else:
            pts = _extract_article_points(summary, article_text)
            pts_html = "".join(f'<li class="p-4 rounded-xl bg-slate-50 border border-slate-200 text-2xl font-semibold text-slate-800">{pt}</li>' for pt in pts[:3])
            center_section = f"""
        <div style="border-color:{th['card_border']};" class="bg-white border-2 rounded-3xl p-7 shadow-md space-y-4 my-3">
          <div class="text-base font-bold text-slate-600 border-b border-slate-100 pb-2">Key takeaways</div>
          <ul class="space-y-3">{pts_html}</ul>
        </div>"""

        clean_kicker = str(spec.get("kicker", "Systems note")).lstrip("/ ").strip()
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800&family=Inter:wght@500;600;700;800&family=JetBrains+Mono:wght@700&display=swap');
    html, body {{ margin:0; padding:0; width:{W}px; height:{H}px; background:{th['bg']}; font-family:'Inter',sans-serif; color:#0F172A; overflow:hidden; }}
    .font-display {{ font-family:'Space Grotesk',sans-serif; }}
    .font-mono {{ font-family:'JetBrains Mono',monospace; }}
    .bg-grid {{ background-image: linear-gradient(to right, {th['grid']} 1px, transparent 1px), linear-gradient(to bottom, {th['grid']} 1px, transparent 1px); background-size: 48px 48px; }}
  </style>
</head>
<body class="bg-grid flex flex-col justify-between p-12">
  <div class="space-y-3">
    <div style="background:{th['kicker_bg']}; border-color:{th['kicker_border']}; color:{th['kicker_text']};" class="inline-block px-4 py-1.5 rounded-full border text-sm font-bold">
      {clean_kicker}
    </div>
    <h1 class="font-display text-5xl font-extrabold text-slate-900 leading-tight tracking-tight">{spec.get('headline', topic)}</h1>
    <p class="text-2xl text-slate-600 font-medium leading-snug">{spec.get('subtitle', summary)}</p>
  </div>

  {center_section}

  {cards_container}

  <div class="flex items-center justify-between border-t-2 border-slate-200 pt-4 text-slate-500 text-base font-semibold">
    <span>{creator} · AI Engineering Notes</span>
    <span>Save for reference</span>
  </div>
</body>
</html>"""

        _render_html_to_png(html, out_png)
        qa_result = _verify_png_with_gemini(topic, out_png)
        if qa_result.get("passed", True) or attempt == 2:
            break
        defects_str = "; ".join(qa_result.get("critical_defects") or [])
        qa_feedback = f"Score {qa_result.get('score', '?')}/100. Defects: {defects_str}. Notes: {qa_result.get('summary', '')}"
        print(f"[linkedin_pro_visuals] Visual QA failed on attempt {attempt}/2 ({qa_feedback}). Regenerating...")

    return {"png_path": str(out_png), "spec": spec, "theme": theme_key, "visual_qa": qa_result}


def render_pro_carousel_pdf(
    topic: str,
    summary: str = "",
    article_text: str = "",
    carousel_plan: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Render a multi-slide 1080x1350 PDF carousel with varied layouts per slide."""
    spec = _build_visual_spec(topic, summary, article_text)
    theme_key = str(spec.get("theme") or _pick_fallback_theme(topic))
    th = THEMES.get(theme_key, THEMES["editorial_paper"])
    svg_html = _sanitize_svg(str(spec.get("svg") or ""))
    slides = spec.get("slides") or []
    if len(slides) < 3 and carousel_plan and isinstance(carousel_plan.get("pages"), list):
        slides = [{"layout": "points", "eyebrow": f"0{i+1}", "title": p.get("heading", topic), "points": [p.get("body", "")]} for i, p in enumerate(carousel_plan["pages"][:5])]

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic.lower()).strip("_")[:32] or "carousel"
    digest = hashlib.md5(topic.encode("utf-8")).hexdigest()[:8]
    out_dir = OUTPUT_DIR / f"carousel_{slug}_{digest}"
    out_dir.mkdir(parents=True, exist_ok=True)
    creator = getattr(config, "CREATOR_NAME", "Vishnu")

    png_paths: List[Path] = []
    total = len(slides)
    for idx, sl in enumerate(slides):
        layout = sl.get("layout", "cover")
        slide_png = out_dir / f"slide_{idx+1:02d}.png"

        if layout == "diagram" and svg_html:
            body_html = f'<div style="border-color:{th["card_border"]};" class="bg-white border-2 rounded-3xl p-6 shadow-md">{svg_html}</div>'
        elif layout == "split":
            body_html = f"""
            <div class="grid grid-cols-1 gap-6">
              <div class="bg-rose-50 border-2 border-rose-300 border-l-8 border-l-rose-600 rounded-2xl p-8 space-y-2">
                <div class="font-mono text-lg font-extrabold text-rose-700">{sl.get('left_title', 'OLD WAY')}</div>
                <p class="text-3xl font-semibold text-slate-800 leading-snug">{sl.get('left_body', '')}</p>
              </div>
              <div class="bg-emerald-50 border-2 border-emerald-400 border-l-8 border-l-emerald-600 rounded-2xl p-8 space-y-2">
                <div class="font-mono text-lg font-extrabold text-emerald-700">{sl.get('right_title', 'NEW WAY')}</div>
                <p class="text-3xl font-semibold text-slate-900 leading-snug">{sl.get('right_body', '')}</p>
              </div>
            </div>"""
        elif layout == "points":
            pts = sl.get("points") or [sl.get("body", "")]
            items = "".join(
                f'<div style="border-color:{th["card_border"]}; border-left-color:{th["accent_a"]};" class="bg-white border-2 border-l-8 rounded-2xl p-6 shadow-sm text-3xl font-semibold text-slate-800">{pt}</div>'
                for pt in pts[:3]
            )
            body_html = f'<div class="space-y-5">{items}</div>'
        elif layout == "cta":
            body_html = f"""
            <div style="border-color:{th['accent_a']};" class="bg-white border-2 rounded-3xl p-10 shadow-lg space-y-6">
              <p class="text-4xl font-bold text-slate-900 leading-snug">{sl.get('body', '')}</p>
              <div class="pt-6 border-t-2 border-slate-100 flex items-center justify-between">
                <div>
                  <div class="text-2xl font-extrabold text-slate-900">{creator}</div>
                  <div class="font-mono text-base text-slate-500">AI Engineering & Systems</div>
                </div>
                <span style="background:{th['accent_a']};" class="px-6 py-3 rounded-xl text-white font-mono text-lg font-extrabold">SAVE & FOLLOW</span>
              </div>
            </div>"""
        else:
            body_html = f'<div style="border-color:{th["card_border"]};" class="bg-white border-2 rounded-3xl p-10 shadow-md"><p class="text-4xl font-semibold text-slate-700 leading-relaxed">{sl.get("body", "")}</p></div>'

        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800&family=Inter:wght@500;600;700;800&family=JetBrains+Mono:wght@700&display=swap');
  html, body {{ margin:0; padding:0; width:{W}px; height:{H}px; background:{th['bg']}; font-family:'Inter',sans-serif; color:#0F172A; overflow:hidden; }}
  .font-display {{ font-family:'Space Grotesk',sans-serif; }} .font-mono {{ font-family:'JetBrains Mono',monospace; }}
  .bg-grid {{ background-image: linear-gradient(to right, {th['grid']} 1px, transparent 1px), linear-gradient(to bottom, {th['grid']} 1px, transparent 1px); background-size: 48px 48px; }}
</style></head>
<body class="bg-grid flex flex-col justify-between p-14">
  <div class="flex items-center justify-between border-b-2 border-slate-200 pb-5 font-mono text-lg font-bold" style="color:{th['accent_a']};">
    <span>{sl.get('eyebrow', f'SLIDE {idx+1}')}</span>
    <span class="text-slate-400">{idx+1} / {total}</span>
  </div>
  <div class="space-y-8 my-auto">
    <h1 class="font-display text-6xl font-extrabold text-slate-900 leading-tight">{sl.get('title', topic)}</h1>
    {body_html}
  </div>
  <div class="flex items-center justify-between border-t-2 border-slate-200 pt-5 font-mono text-base font-bold text-slate-500">
    <span>{creator} · AI Engineering</span>
    <span>{'SWIPE →' if idx + 1 < total else 'DONE'}</span>
  </div>
</body></html>"""
        _render_html_to_png(html, slide_png)
        png_paths.append(slide_png)

    pdf_path = out_dir / f"{slug}_carousel.pdf"
    imgs = [Image.open(p).convert("RGB") for p in png_paths]
    if imgs:
        imgs[0].save(str(pdf_path), save_all=True, append_images=imgs[1:])
    return {"pdf_path": str(pdf_path), "slide_count": len(png_paths), "first_slide_png": str(png_paths[0]) if png_paths else None, "theme": theme_key}
