import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright

CAROUSEL_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "AI_SERIES" / "CAROUSELS"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');
  
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  
  body {{
    width: 1080px;
    height: 1350px;
    background: radial-gradient(circle at 80% 10%, #151f38 0%, #070a14 70%);
    color: #F8FAFC;
    font-family: 'Plus Jakarta Sans', sans-serif;
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 70px 75px 60px 75px;
  }}
  
  /* Top Glow Mesh */
  .glow-top {{
    position: absolute;
    top: -150px;
    right: -100px;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(56, 189, 248, 0.15) 0%, rgba(56, 189, 248, 0) 70%);
    pointer-events: none;
  }}

  .glow-bottom {{
    position: absolute;
    bottom: -150px;
    left: -100px;
    width: 550px;
    height: 550px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, rgba(99, 102, 241, 0) 70%);
    pointer-events: none;
  }}

  /* Header Bar */
  .header-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 10;
  }}

  .series-tag {{
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 8px 18px;
    background: rgba(56, 189, 248, 0.08);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 999px;
    font-size: 16px;
    font-weight: 700;
    color: #38BDF8;
    text-transform: uppercase;
    letter-spacing: 1.5px;
  }}

  .slide-counter {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 19px;
    color: #64748B;
    font-weight: 700;
    background: rgba(255, 255, 255, 0.03);
    padding: 6px 16px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.08);
  }}

  /* Main Card Layout */
  .main-stage {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 24px;
    z-index: 10;
  }}

  .category-pill {{
    align-self: flex-start;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 6px 14px;
    border-radius: 8px;
    text-transform: uppercase;
  }}
  .pill-cyan {{ background: rgba(56, 189, 248, 0.15); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.3); }}
  .pill-red {{ background: rgba(244, 63, 94, 0.15); color: #FB7185; border: 1px solid rgba(244, 63, 94, 0.3); }}
  .pill-emerald {{ background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }}

  .hero-heading {{
    font-size: 42px;
    font-weight: 800;
    line-height: 1.25;
    background: linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 60%, #94A3B8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}

  .glass-card {{
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(56, 189, 248, 0.22);
    border-radius: 24px;
    padding: 30px 34px;
    backdrop-filter: blur(20px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    display: flex;
    flex-direction: column;
    gap: 18px;
  }}

  .flow-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }}

  .flow-panel {{
    background: rgba(2, 6, 23, 0.7);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.06);
  }}

  .flow-title {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 12px;
    text-transform: uppercase;
  }}

  .code-snip {{
    background: #020617;
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 14px;
    padding: 20px 22px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 19px;
    line-height: 1.6;
  }}
  .kw {{ color: #F43F5E; }}
  .fn {{ color: #38BDF8; }}
  .str {{ color: #34D399; }}
  .com {{ color: #64748B; font-style: italic; }}

  .takeaway-banner {{
    display: flex;
    align-items: center;
    gap: 14px;
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.3);
    padding: 18px 24px;
    border-radius: 16px;
    font-size: 20px;
    line-height: 1.45;
    color: #E2E8F0;
  }}

  /* Footer Bar */
  .footer-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 25px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    z-index: 10;
  }}

  .brand-group {{
    display: flex;
    align-items: center;
    gap: 14px;
  }}

  .brand-logo {{
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: linear-gradient(135deg, #38BDF8, #6366F1);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 20px;
    color: #020617;
  }}

  .brand-meta {{
    display: flex;
    flex-direction: column;
  }}

  .brand-name {{
    font-weight: 700;
    font-size: 18px;
    color: #F8FAFC;
  }}

  .brand-handle {{
    font-size: 14px;
    color: #64748B;
  }}

  .cta-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 15px;
    color: #38BDF8;
    background: rgba(56, 189, 248, 0.08);
    padding: 8px 18px;
    border-radius: 20px;
    border: 1px solid rgba(56, 189, 248, 0.2);
  }}
</style>
</head>
<body>
  <div class="glow-top"></div>
  <div class="glow-bottom"></div>

  <!-- Header -->
  <div class="header-bar">
    <div class="series-tag">🧠 {series_title}</div>
    <div class="slide-counter">{current_slide} / {total_slides}</div>
  </div>

  <!-- Main Content Stage -->
  <div class="main-stage">
    {content_html}
  </div>

  <!-- Footer -->
  <div class="footer-bar">
    <div class="brand-group">
      <div class="brand-logo">N</div>
      <div class="brand-meta">
        <span class="brand-name">NeuBench</span>
        <span class="brand-handle">@neubench • Live AI Benchmarks</span>
      </div>
    </div>
    <div class="cta-tag">{cta_text}</div>
  </div>
</body>
</html>
"""

class InstagramCarouselGenerator:
    """Generates enriched 1080x1350 technical carousel PNG slides with syntax highlighting and architecture comparisons."""

    def __init__(self):
        CAROUSEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def render_slides(self, day: int, topic: str, slides_data: List[Dict[str, Any]]) -> List[str]:
        """Renders slides_data into 1080x1350 PNG images using Playwright and returns file paths."""
        day_dir = CAROUSEL_OUTPUT_DIR / f"DAY_{day:03d}"
        day_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []
        total_slides = len(slides_data)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1080, "height": 1350})

            for idx, slide in enumerate(slides_data, start=1):
                cta = slide.get("cta", "Swipe to Learn ➔" if idx < total_slides else "📌 Save for Revision")
                full_html = HTML_TEMPLATE.format(
                    series_title=f"AI Masterclass • Day {day:02d}",
                    current_slide=f"{idx:02d}",
                    total_slides=f"{total_slides:02d}",
                    content_html=slide["html"],
                    cta_text=cta
                )

                page.set_content(full_html)
                page.wait_for_timeout(800)
                output_path = day_dir / f"slide_{idx:02d}.png"
                page.screenshot(path=str(output_path), type="png")
                generated_files.append(str(output_path))

            browser.close()

        return generated_files

    def build_day1_sample(self) -> List[str]:
        """Builds the enriched high-density Day 1 5-slide visual cheatsheet."""
        slides = [
            # Slide 1: Cover
            {
                "cta": "Swipe to Learn ➔",
                "html": """
                <div class="category-pill pill-cyan">DAY 01 OF 90 • ARCHITECTURE MODEL</div>
                <h1 class="hero-heading" style="font-size: 54px; line-height: 1.15;">
                  What is Artificial Intelligence?
                </h1>
                <div style="font-size: 26px; line-height: 1.5; color: #94A3B8;">
                  Rules-based code vs. learned behavior: The fundamental engineering shift of the modern era.
                </div>
                <div class="glass-card" style="margin-top: 10px;">
                  <div style="display: flex; align-items: center; gap: 14px; font-size: 20px; color: #F1F5F9;">
                    <span>⚡ <b>Level 1:</b> AI Fundamentals</span>
                    <span style="color: #64748B;">•</span>
                    <span>📂 <b>Chapter:</b> The Core Mental Model</span>
                  </div>
                  <div style="font-size: 18px; color: #CBD5E1; line-height: 1.5;">
                    Most engineers get stuck thinking AI is magical sentient code. In reality, it is simply an inversion of the classical compute pipeline.
                  </div>
                </div>
                """
            },
            # Slide 2: The Core Paradigm Shift
            {
                "cta": "Swipe for Details ➔",
                "html": """
                <div class="category-pill pill-cyan">THE CORE INVERSION</div>
                <h1 class="hero-heading" style="font-size: 40px;">How the Equation Flips</h1>
                
                <div class="flow-grid">
                  <div class="flow-panel">
                    <div class="flow-title" style="color: #FB7185;">⚙️ Classical Software</div>
                    <div style="font-size: 18px; color: #CBD5E1; margin-bottom: 10px;">
                      Data + Rules ➔ <b>Answers</b>
                    </div>
                    <div style="font-size: 15px; color: #94A3B8; line-height: 1.4;">
                      Humans handcraft deterministic if/else conditions. Fragile when edge-cases proliferate.
                    </div>
                  </div>
                  
                  <div class="flow-panel">
                    <div class="flow-title" style="color: #34D399;">🧠 Machine Learning</div>
                    <div style="font-size: 18px; color: #CBD5E1; margin-bottom: 10px;">
                      Data + Answers ➔ <b>Rules (Weights)</b>
                    </div>
                    <div style="font-size: 15px; color: #94A3B8; line-height: 1.4;">
                      Algorithms synthesize high-dimensional mathematical functions directly from data.
                    </div>
                  </div>
                </div>

                <div class="code-snip">
                  <span class="com"># Classical: developer codes every edge case</span><br>
                  <span class="kw">if</span> <span class="str">"urgent transfer"</span> <span class="kw">in</span> email: <span class="kw">return</span> <span class="str">"SPAM"</span><br>
                  <span class="com"># ML: model learns continuous representations</span><br>
                  model.<span class="fn">fit</span>(X_emails, y_labels) <span class="com"># learns 10,000 fuzzy features</span>
                </div>
                """
            },
            # Slide 3: The Classical Trap
            {
                "cta": "Swipe to Compare ➔",
                "html": """
                <div class="category-pill pill-red">ENGINEERING PITFALL</div>
                <h1 class="hero-heading" style="font-size: 38px;">Why Hardcoded Rules Break</h1>
                
                <div class="glass-card">
                  <div style="font-size: 22px; font-weight: 700; color: #F1F5F9;">
                    The Combinatorial Explosion Problem
                  </div>
                  <div style="font-size: 19px; line-height: 1.5; color: #CBD5E1;">
                    Say you build a spam detector using regular expressions. Spammers write:
                  </div>
                  <div class="code-snip" style="font-size: 17px;">
                    <span class="str">"fr33 m0ney"</span> | <span class="str">"f-r-e-e"</span> | <span class="str">"c!ick here"</span> | <span class="str">"w!n prize"</span>
                  </div>
                  <div style="font-size: 18px; line-height: 1.5; color: #FB7185;">
                    ⚠️ <b>The Rule Trap:</b> Your codebase balloons to 4,000 nested regexes. Latency spikes, and false positives destroy user trust.
                  </div>
                </div>

                <div class="takeaway-banner">
                  💡 <b>Key Lesson:</b> Static rules scale linearly with engineer burnout. Statistical models adapt dynamically with new data.
                </div>
                """
            },
            # Slide 4: When to Use AI vs Code
            {
                "cta": "Swipe for Summary ➔",
                "html": """
                <div class="category-pill pill-emerald">DECISION MATRIX</div>
                <h1 class="hero-heading" style="font-size: 38px;">When Should You Use AI?</h1>

                <div class="flow-grid">
                  <div class="flow-panel" style="border-color: rgba(244, 63, 94, 0.3);">
                    <div class="flow-title" style="color: #FB7185;">❌ DO NOT Use AI</div>
                    <ul style="font-size: 16px; color: #CBD5E1; line-height: 1.6; margin-left: 18px;">
                      <li>Payroll & tax calculations</li>
                      <li>Order discount rules</li>
                      <li>Deterministic auth & routing</li>
                      <li>Fixed schema validation</li>
                    </ul>
                  </div>

                  <div class="flow-panel" style="border-color: rgba(52, 211, 153, 0.3);">
                    <div class="flow-title" style="color: #34D399;">✅ DO Use AI</div>
                    <ul style="font-size: 16px; color: #CBD5E1; line-height: 1.6; margin-left: 18px;">
                      <li>Unstructured text & vision</li>
                      <li>Semantic search & embeddings</li>
                      <li>Anomaly & fraud detection</li>
                      <li>Complex voice synthesis</li>
                    </ul>
                  </div>
                </div>

                <div class="takeaway-banner" style="background: rgba(56, 189, 248, 0.08); border-color: rgba(56, 189, 248, 0.25);">
                  📌 <b>Golden Rule:</b> If a deterministic function is 100% accurate and fast, never replace it with a probabilistic model.
                </div>
                """
            },
            # Slide 5: Cheatsheet & Save
            {
                "cta": "📌 Save for Revision",
                "html": """
                <div class="category-pill pill-cyan">DAY 01 RECAP • 1-PAGE SUMMARY</div>
                <h1 class="hero-heading" style="font-size: 40px;">Day 01 Cheatsheet</h1>

                <div class="glass-card">
                  <div style="font-size: 20px; line-height: 1.6; color: #E2E8F0; display: flex; flex-direction: column; gap: 14px;">
                    <div>1️⃣ <b>The Inversion:</b> Code writes rules; ML algorithms learn rules from data.</div>
                    <div>2️⃣ <b>Weight Optimization:</b> "Learning" means adjusting continuous numeric weights to minimize loss.</div>
                    <div>3️⃣ <b>Data Quality:</b> In ML, data is your source code. Garbage data produces garbage weights.</div>
                  </div>
                </div>

                <div class="glass-card" style="border-color: #38BDF8; background: rgba(56, 189, 248, 0.06); text-align: center;">
                  <div style="font-size: 22px; font-weight: 800; color: #38BDF8; margin-bottom: 8px;">
                    Tomorrow: Day 02
                  </div>
                  <div style="font-size: 19px; color: #F1F5F9;">
                    Symbolic AI vs. Statistical Learning: Why expert systems lost and neural nets won.
                  </div>
                </div>
                """
            }
        ]

        return self.render_slides(day=1, topic="What is Artificial Intelligence?", slides_data=slides)

if __name__ == "__main__":
    generator = InstagramCarouselGenerator()
    paths = generator.build_day1_sample()
    print(f"Generated {len(paths)} enriched slides successfully!")
