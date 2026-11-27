"""Pro LinkedIn Visuals Engine (Playwright HTML/CSS/SVG -> 1080x1350 PNG & Multi-Slide PDF Carousel).

Replaces rigid Pillow boilerplate diagrams with crisp Light-Mode editorial layouts
and bespoke topic-specific SVG architecture/workflow diagrams driven by the actual article.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

import config

OUTPUT_DIR = Path("generated_visuals") / "linkedin"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1350


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
        svg = svg.replace("<svg", '<svg viewBox="0 0 920 460"', 1)
    svg = re.sub(
        r"<svg([^>]*)>",
        lambda g: "<svg"
        + re.sub(r'\s(width|height)\s*=\s*["\'][^"\']*["\']', "", g.group(1))
        + ' class="w-full h-auto max-h-[500px]">',
        svg,
        count=1,
    )
    return svg


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


def _build_visual_spec(topic: str, summary: str, article_text: str) -> Dict[str, Any]:
    prompt = f"""You are a senior staff engineer & editorial designer (ByteByteGo / Stripe Docs / Apple Keynote).
Design a crystal-clear Light-Mode LinkedIn visual attachment for this exact post:

Topic: {topic}
Summary: {summary}
Article Excerpt: {article_text[:1200]}

STRICT RULES:
- ZERO generic boilerplate ("Payload Dispatch", "State Evaluation", "Downstream Commit", "Strict bounded memory pool").
- Every label, node, and metric MUST be 100% specific to "{topic}".
- Write a crisp inline `<svg viewBox="0 0 920 440">` diagram on a clean light background (`#F8FAFC` / `#FFFFFF`), dark slate ink (`#0F172A`), and sharp accents (`#0284C7` blue, `#059669` emerald, `#E11D48` rose, `#D97706` amber). Minimum `font-size="20"` inside SVG so text is never tiny or truncated.
- Return ONLY valid JSON:
{{
  "kicker": "SHORT CATEGORY TAG (e.g. SYSTEMS ARCHITECTURE)",
  "headline": "Sharp 4-8 word title",
  "subtitle": "One concrete sentence explaining the core mechanism.",
  "diagram_title": "1. HOW IT ACTUALLY WORKS",
  "svg": "<svg viewBox='0 0 920 440'>...</svg>",
  "takeaways": [
    {{"tag": "01 // MECHANISM", "title": "Short title", "body": "Concrete 1-sentence insight from the article."}},
    {{"tag": "02 // TRADEOFF", "title": "Short title", "body": "Concrete 1-sentence tradeoff or failure mode."}}
  ],
  "slides": [
    {{"eyebrow": "01 // THE HOOK", "title": "Bold cover headline", "body": "Why this matters right now."}},
    {{"eyebrow": "02 // THE BOTTLENECK", "title": "What breaks without it", "body": "Concrete limitation or bottleneck."}},
    {{"eyebrow": "03 // ARCHITECTURE", "title": "How it works", "body": "Step-by-step data flow.", "use_svg": true}},
    {{"eyebrow": "04 // PRODUCTION REALITY", "title": "Key tradeoffs", "body": "Cost, latency, or accuracy reality."}},
    {{"eyebrow": "05 // TAKEAWAY", "title": "What to do next", "body": "One actionable rule for builders."}}
  ]
}}"""
    parsed = _call_gemini_json(prompt)
    if parsed and isinstance(parsed.get("takeaways"), list):
        return parsed

    # Clean topic-specific fallback (zero generic boilerplate)
    return {
        "kicker": "ENGINEERING NOTES",
        "headline": topic[:64],
        "subtitle": summary[:130] or f"How {topic} works in production.",
        "diagram_title": "1. CORE MECHANISM",
        "svg": f"""<svg viewBox="0 0 920 440" xmlns="http://www.w3.org/2000/svg">
          <rect width="920" height="440" rx="18" fill="#F8FAFC"/>
          <rect x="40" y="140" width="240" height="150" rx="16" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="3"/>
          <text x="160" y="205" font-family="Inter, sans-serif" font-size="22" font-weight="800" fill="#0F172A" text-anchor="middle">INPUT</text>
          <text x="160" y="242" font-family="Inter, sans-serif" font-size="18" fill="#475569" text-anchor="middle">Raw Request</text>
          <line x1="280" y1="215" x2="340" y2="215" stroke="#0284C7" stroke-width="4"/>
          <rect x="340" y="120" width="240" height="190" rx="16" fill="#EFF6FF" stroke="#0284C7" stroke-width="3"/>
          <text x="460" y="200" font-family="Inter, sans-serif" font-size="22" font-weight="800" fill="#0369A1" text-anchor="middle">CORE ENGINE</text>
          <text x="460" y="240" font-family="Inter, sans-serif" font-size="18" fill="#1E293B" text-anchor="middle">{topic[:20]}</text>
          <line x1="580" y1="215" x2="640" y2="215" stroke="#059669" stroke-width="4"/>
          <rect x="640" y="140" width="240" height="150" rx="16" fill="#ECFDF5" stroke="#059669" stroke-width="3"/>
          <text x="760" y="205" font-family="Inter, sans-serif" font-size="22" font-weight="800" fill="#047857" text-anchor="middle">OUTPUT</text>
          <text x="760" y="242" font-family="Inter, sans-serif" font-size="18" fill="#065F46" text-anchor="middle">Verified Result</text>
        </svg>""",
        "takeaways": [
            {"tag": "01 // CORE IDEA", "title": "Why It Matters", "body": summary[:140] or topic},
            {"tag": "02 // PRODUCTION NOTE", "title": "Builder Takeaway", "body": "Measure latency, cost, and accuracy before scaling."},
        ],
        "slides": [
            {"eyebrow": "01 // OVERVIEW", "title": topic[:55], "body": summary[:160] or topic},
            {"eyebrow": "02 // ARCHITECTURE", "title": "System Flow", "body": summary[:140] or topic, "use_svg": True},
            {"eyebrow": "03 // TAKEAWAY", "title": "Key Lesson", "body": "Measure real bottlenecks before optimizing."},
        ],
    }


def _render_html_to_png(html_str: str, out_png: Path) -> None:
    from playwright.sync_api import sync_playwright
    tmp_html = out_png.with_suffix(".html")
    tmp_html.write_text(html_str, encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(tmp_html.resolve().as_uri(), wait_until="networkidle")
        page.wait_for_timeout(350)
        page.screenshot(path=str(out_png), type="png")
        browser.close()


def render_pro_architecture_png(topic: str, summary: str = "", article_text: str = "") -> Dict[str, Any]:
    """Render a crisp 1080x1350 Light-Mode editorial architecture PNG via Playwright."""
    spec = _build_visual_spec(topic, summary, article_text)
    svg_html = _sanitize_svg(str(spec.get("svg") or ""))
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic.lower()).strip("_")[:32] or "post"
    digest = hashlib.md5(topic.encode("utf-8")).hexdigest()[:8]
    out_dir = OUTPUT_DIR / f"pro_{slug}_{digest}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_png = out_dir / f"{slug}.png"

    creator = getattr(config, "CREATOR_NAME", "Vishnu")
    cards_html = ""
    for item in (spec.get("takeaways") or [])[:2]:
        cards_html += f"""
        <div class="bg-white border-2 border-slate-200 rounded-2xl p-6 shadow-sm space-y-1.5">
          <div class="font-mono text-sm font-extrabold tracking-widest text-sky-600 uppercase">{item.get('tag', '')}</div>
          <div class="text-2xl font-extrabold text-slate-900">{item.get('title', '')}</div>
          <p class="text-xl text-slate-600 leading-snug font-medium">{item.get('body', '')}</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800&family=Inter:wght@500;600;700;800&family=JetBrains+Mono:wght@700&display=swap');
    html, body {{ margin:0; padding:0; width:{W}px; height:{H}px; background:#FAF9F6; font-family:'Inter',sans-serif; color:#0F172A; overflow:hidden; }}
    .font-display {{ font-family:'Space Grotesk',sans-serif; }}
    .font-mono {{ font-family:'JetBrains Mono',monospace; }}
    .bg-grid {{ background-image: linear-gradient(to right, rgba(15,23,42,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(15,23,42,0.04) 1px, transparent 1px); background-size: 48px 48px; }}
  </style>
</head>
<body class="bg-grid flex flex-col justify-between p-12">
  <div class="space-y-4">
    <div class="inline-block px-4 py-1.5 rounded-full bg-sky-100 border border-sky-300 font-mono text-sm font-extrabold text-sky-800 tracking-widest uppercase">
      // {spec.get('kicker', 'SYSTEMS NOTE')}
    </div>
    <h1 class="font-display text-5xl font-extrabold text-slate-900 leading-tight tracking-tight">{spec.get('headline', topic)}</h1>
    <p class="text-2xl text-slate-600 font-medium leading-snug">{spec.get('subtitle', summary)}</p>
  </div>

  <div class="bg-white border-2 border-slate-200 rounded-3xl p-6 shadow-md space-y-3 my-4">
    <div class="font-mono text-base font-extrabold text-slate-500 tracking-wider uppercase border-b border-slate-100 pb-2">
      {spec.get('diagram_title', '1. ARCHITECTURE')}
    </div>
    <div class="rounded-2xl bg-slate-50 border border-slate-200 p-3 flex items-center justify-center">
      {svg_html}
    </div>
  </div>

  <div class="space-y-4">
    {cards_html}
  </div>

  <div class="flex items-center justify-between border-t-2 border-slate-200 pt-4 text-slate-500 font-mono text-base font-bold">
    <span>{creator} · AI Engineering Notes</span>
    <span>SWIPE / SAVE FOR LATER</span>
  </div>
</body>
</html>"""

    _render_html_to_png(html, out_png)
    return {"png_path": str(out_png), "spec": spec}


def render_pro_carousel_pdf(
    topic: str,
    summary: str = "",
    article_text: str = "",
    carousel_plan: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Render a multi-slide 1080x1350 PDF carousel via Playwright + Pillow."""
    spec = _build_visual_spec(topic, summary, article_text)
    svg_html = _sanitize_svg(str(spec.get("svg") or ""))
    slides = spec.get("slides") or []
    if len(slides) < 3 and carousel_plan and isinstance(carousel_plan.get("pages"), list):
        slides = [{"eyebrow": f"0{i+1}", "title": p.get("heading", topic), "body": p.get("body", "")} for i, p in enumerate(carousel_plan["pages"][:5])]

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic.lower()).strip("_")[:32] or "carousel"
    digest = hashlib.md5(topic.encode("utf-8")).hexdigest()[:8]
    out_dir = OUTPUT_DIR / f"carousel_{slug}_{digest}"
    out_dir.mkdir(parents=True, exist_ok=True)
    creator = getattr(config, "CREATOR_NAME", "Vishnu")

    png_paths: List[Path] = []
    total = len(slides)
    for idx, sl in enumerate(slides):
        use_svg = bool(sl.get("use_svg")) and bool(svg_html)
        slide_png = out_dir / f"slide_{idx+1:02d}.png"
        center_block = (
            f'<div class="bg-white border-2 border-slate-200 rounded-3xl p-6 shadow-md">{svg_html}</div>'
            if use_svg
            else f'<div class="bg-white border-2 border-slate-200 rounded-3xl p-10 shadow-md"><p class="text-4xl font-semibold text-slate-700 leading-relaxed">{sl.get("body", "")}</p></div>'
        )
        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800&family=Inter:wght@500;600;700;800&family=JetBrains+Mono:wght@700&display=swap');
  html, body {{ margin:0; padding:0; width:{W}px; height:{H}px; background:#FAF9F6; font-family:'Inter',sans-serif; color:#0F172A; overflow:hidden; }}
  .font-display {{ font-family:'Space Grotesk',sans-serif; }} .font-mono {{ font-family:'JetBrains Mono',monospace; }}
</style></head>
<body class="flex flex-col justify-between p-14">
  <div class="flex items-center justify-between border-b-2 border-slate-200 pb-5 font-mono text-lg font-bold text-sky-700">
    <span>{sl.get('eyebrow', f'SLIDE {idx+1}')}</span>
    <span class="text-slate-400">{idx+1} / {total}</span>
  </div>
  <div class="space-y-8 my-auto">
    <h1 class="font-display text-6xl font-extrabold text-slate-900 leading-tight">{sl.get('title', topic)}</h1>
    {center_block}
  </div>
  <div class="flex items-center justify-between border-t-2 border-slate-200 pt-5 font-mono text-base font-bold text-slate-500">
    <span>{creator} · AI Engineering</span>
    <span>{'SWIPE →' if idx + 1 < total else 'SAVE & FOLLOW'}</span>
  </div>
</body></html>"""
        _render_html_to_png(html, slide_png)
        png_paths.append(slide_png)

    pdf_path = out_dir / f"{slug}_carousel.pdf"
    imgs = [Image.open(p).convert("RGB") for p in png_paths]
    if imgs:
        imgs[0].save(str(pdf_path), save_all=True, append_images=imgs[1:])
    return {"pdf_path": str(pdf_path), "slide_count": len(png_paths), "first_slide_png": str(png_paths[0]) if png_paths else None}
