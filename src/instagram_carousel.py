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
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap');
  
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
    padding: 65px 70px 55px 70px;
  }}
  
  /* Top Glow Mesh */
  .glow-top {{
    position: absolute;
    top: -150px;
    right: -100px;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(56, 189, 248, 0.16) 0%, rgba(56, 189, 248, 0) 70%);
    pointer-events: none;
  }}

  .glow-bottom {{
    position: absolute;
    bottom: -150px;
    left: -100px;
    width: 550px;
    height: 550px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.14) 0%, rgba(99, 102, 241, 0) 70%);
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
    gap: 12px;
    padding: 10px 22px;
    background: rgba(56, 189, 248, 0.1);
    border: 1.5px solid rgba(56, 189, 248, 0.3);
    border-radius: 999px;
    font-size: 19px;
    font-weight: 700;
    color: #38BDF8;
    text-transform: uppercase;
    letter-spacing: 1.5px;
  }}

  .slide-counter {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 22px;
    color: #94A3B8;
    font-weight: 700;
    background: rgba(255, 255, 255, 0.05);
    padding: 8px 20px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }}

  /* Main Card Layout */
  .main-stage {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 26px;
    z-index: 10;
  }}

  .category-pill {{
    align-self: flex-start;
    font-family: 'JetBrains Mono', monospace;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 1.2px;
    padding: 8px 18px;
    border-radius: 10px;
    text-transform: uppercase;
  }}
  .pill-cyan {{ background: rgba(56, 189, 248, 0.18); color: #38BDF8; border: 1.5px solid rgba(56, 189, 248, 0.35); }}
  .pill-red {{ background: rgba(244, 63, 94, 0.18); color: #FB7185; border: 1.5px solid rgba(244, 63, 94, 0.35); }}
  .pill-emerald {{ background: rgba(16, 185, 129, 0.18); color: #34D399; border: 1.5px solid rgba(16, 185, 129, 0.35); }}

  .hero-heading {{
    font-size: 48px;
    font-weight: 800;
    line-height: 1.22;
    background: linear-gradient(135deg, #FFFFFF 0%, #F1F5F9 60%, #CBD5E1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}

  .glass-card {{
    background: rgba(15, 23, 42, 0.78);
    border: 1.5px solid rgba(56, 189, 248, 0.28);
    border-radius: 26px;
    padding: 34px 38px;
    backdrop-filter: blur(24px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.45);
    display: flex;
    flex-direction: column;
    gap: 20px;
  }}

  .flow-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }}

  .flow-panel {{
    background: rgba(2, 6, 23, 0.85);
    border-radius: 20px;
    padding: 24px;
    border: 1.5px solid rgba(255, 255, 255, 0.1);
  }}

  .flow-title {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 14px;
    text-transform: uppercase;
  }}

  .code-snip {{
    background: #020617;
    border: 1.5px solid rgba(148, 163, 184, 0.18);
    border-radius: 18px;
    padding: 24px 26px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 23px;
    line-height: 1.6;
  }}
  .kw {{ color: #F43F5E; font-weight: 700; }}
  .fn {{ color: #38BDF8; font-weight: 700; }}
  .str {{ color: #34D399; }}
  .com {{ color: #64748B; font-style: italic; }}

  .takeaway-banner {{
    display: flex;
    align-items: center;
    gap: 16px;
    background: rgba(99, 102, 241, 0.14);
    border: 1.5px solid rgba(99, 102, 241, 0.35);
    padding: 22px 28px;
    border-radius: 18px;
    font-size: 24px;
    line-height: 1.45;
    color: #F1F5F9;
  }}

  /* Footer Bar */
  .footer-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 25px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    z-index: 10;
  }}

  .brand-group {{
    display: flex;
    align-items: center;
    gap: 16px;
  }}

  .brand-logo {{
    width: 50px;
    height: 50px;
    border-radius: 14px;
    background: linear-gradient(135deg, #38BDF8, #6366F1);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 24px;
    color: #020617;
  }}

  .brand-meta {{
    display: flex;
    flex-direction: column;
  }}

  .brand-name {{
    font-weight: 700;
    font-size: 22px;
    color: #F8FAFC;
  }}

  .brand-handle {{
    font-size: 16px;
    color: #94A3B8;
  }}

  .cta-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 18px;
    font-weight: 700;
    color: #38BDF8;
    background: rgba(56, 189, 248, 0.12);
    padding: 10px 22px;
    border-radius: 22px;
    border: 1.5px solid rgba(56, 189, 248, 0.3);
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
    """Generates enriched 1080x1350 technical carousel PNG slides with syntax highlighting and clear, high-legibility typography."""

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
        """Builds the enriched high-density Day 1 5-slide visual cheatsheet with large readable fonts."""
        slides = [
            # Slide 1: Cover
            {
                "cta": "Swipe to Learn ➔",
                "html": """
                <div class="category-pill pill-cyan">DAY 01 OF 90 • ARCHITECTURE MODEL</div>
                <h1 class="hero-heading" style="font-size: 58px; line-height: 1.15;">
                  What is Artificial Intelligence?
                </h1>
                <div style="font-size: 30px; line-height: 1.5; color: #CBD5E1;">
                  Rules-based code vs. learned behavior: The fundamental engineering shift of modern software.
                </div>
                <div class="glass-card" style="margin-top: 10px;">
                  <div style="display: flex; align-items: center; gap: 16px; font-size: 24px; color: #F1F5F9;">
                    <span>⚡ <b>Level 1:</b> AI Fundamentals</span>
                    <span style="color: #64748B;">•</span>
                    <span>📂 <b>Chapter:</b> The Core Mental Model</span>
                  </div>
                  <div style="font-size: 24px; color: #E2E8F0; line-height: 1.55;">
                    Most engineers think AI is sentient code or mysterious math. In reality, it is simply a mathematical inversion of the classical software pipeline.
                  </div>
                </div>
                """
            },
            # Slide 2: The Core Paradigm Shift
            {
                "cta": "Swipe for Details ➔",
                "html": """
                <div class="category-pill pill-cyan">THE CORE INVERSION</div>
                <h1 class="hero-heading" style="font-size: 46px;">How the Equation Flips</h1>
                
                <div class="flow-grid">
                  <div class="flow-panel">
                    <div class="flow-title" style="color: #FB7185;">⚙️ Classical Software</div>
                    <div style="font-size: 23px; color: #F8FAFC; margin-bottom: 10px;">
                      Data + Rules ➔ <b>Answers</b>
                    </div>
                    <div style="font-size: 20px; color: #CBD5E1; line-height: 1.45;">
                      Developers handcraft deterministic if/else rules. Brittle when edge cases proliferate.
                    </div>
                  </div>
                  
                  <div class="flow-panel">
                    <div class="flow-title" style="color: #34D399;">🧠 Machine Learning</div>
                    <div style="font-size: 23px; color: #F8FAFC; margin-bottom: 10px;">
                      Data + Answers ➔ <b>Rules</b>
                    </div>
                    <div style="font-size: 20px; color: #CBD5E1; line-height: 1.45;">
                      Algorithms synthesize continuous mathematical parameters directly from training data.
                    </div>
                  </div>
                </div>

                <div class="code-snip">
                  <span class="com"># Classical: developer codes every edge case</span><br>
                  <span class="kw">if</span> <span class="str">"urgent wire"</span> <span class="kw">in</span> email: <span class="kw">return</span> <span class="str">"SPAM"</span><br>
                  <span class="com"># ML: model learns continuous representations</span><br>
                  model.<span class="fn">fit</span>(X_emails, y_labels) <span class="com"># learns 10k fuzzy features</span>
                </div>
                """
            },
            # Slide 3: The Classical Trap
            {
                "cta": "Swipe to Compare ➔",
                "html": """
                <div class="category-pill pill-red">ENGINEERING PITFALL</div>
                <h1 class="hero-heading" style="font-size: 44px;">Why Hardcoded Rules Break</h1>
                
                <div class="glass-card">
                  <div style="font-size: 26px; font-weight: 700; color: #F1F5F9;">
                    The Combinatorial Explosion Problem
                  </div>
                  <div style="font-size: 23px; line-height: 1.5; color: #CBD5E1;">
                    When you build detection logic with regular expressions, adversaries bypass you with simple character swaps:
                  </div>
                  <div class="code-snip" style="font-size: 22px;">
                    <span class="str">"fr33 m0ney"</span> | <span class="str">"f-r-e-e"</span> | <span class="str">"c!ick here"</span>
                  </div>
                  <div style="font-size: 22px; line-height: 1.5; color: #FB7185;">
                    ⚠️ <b>The Rule Trap:</b> Your codebase balloons into 4,000 brittle regex rules. Latency spikes and false positives explode.
                  </div>
                </div>

                <div class="takeaway-banner">
                  💡 <b>Key Lesson:</b> Static rules scale with developer burnout. Machine learning scales dynamically with data.
                </div>
                """
            },
            # Slide 4: When to Use AI vs Code
            {
                "cta": "Swipe for Summary ➔",
                "html": """
                <div class="category-pill pill-emerald">DECISION MATRIX</div>
                <h1 class="hero-heading" style="font-size: 44px;">When Should You Use AI?</h1>

                <div class="flow-grid">
                  <div class="flow-panel" style="border-color: rgba(244, 63, 94, 0.4);">
                    <div class="flow-title" style="color: #FB7185;">❌ DO NOT Use AI</div>
                    <ul style="font-size: 21px; color: #E2E8F0; line-height: 1.7; margin-left: 22px;">
                      <li>Payroll & tax calculations</li>
                      <li>Order discount logic</li>
                      <li>Deterministic auth / routing</li>
                      <li>Fixed schema validation</li>
                    </ul>
                  </div>

                  <div class="flow-panel" style="border-color: rgba(52, 211, 153, 0.4);">
                    <div class="flow-title" style="color: #34D399;">✅ DO Use AI</div>
                    <ul style="font-size: 21px; color: #E2E8F0; line-height: 1.7; margin-left: 22px;">
                      <li>Unstructured text & vision</li>
                      <li>Semantic search & embeddings</li>
                      <li>Anomaly & fraud detection</li>
                      <li>Neural voice & speech synthesis</li>
                    </ul>
                  </div>
                </div>

                <div class="takeaway-banner" style="background: rgba(56, 189, 248, 0.1); border-color: rgba(56, 189, 248, 0.3);">
                  📌 <b>Rule of Thumb:</b> If deterministic logic solves it with 100% precision, never replace it with a probabilistic model.
                </div>
                """
            },
            # Slide 5: Cheatsheet & Save
            {
                "cta": "📌 Save for Revision",
                "html": """
                <div class="category-pill pill-cyan">DAY 01 RECAP • 1-PAGE SUMMARY</div>
                <h1 class="hero-heading" style="font-size: 46px;">Day 01 Cheatsheet</h1>

                <div class="glass-card">
                  <div style="font-size: 24px; line-height: 1.6; color: #F1F5F9; display: flex; flex-direction: column; gap: 16px;">
                    <div>1️⃣ <b>The Inversion:</b> Code handcrafts rules; ML algorithms learn rules directly from data.</div>
                    <div>2️⃣ <b>Weight Optimization:</b> Learning is simply adjusting continuous numeric weights to minimize loss.</div>
                    <div>3️⃣ <b>Data Quality:</b> In ML, data is your source code. Dirty data creates broken weights.</div>
                  </div>
                </div>

                <div class="glass-card" style="border-color: #38BDF8; background: rgba(56, 189, 248, 0.08); text-align: center;">
                  <div style="font-size: 25px; font-weight: 800; color: #38BDF8; margin-bottom: 8px;">
                    Tomorrow: Day 02
                  </div>
                  <div style="font-size: 22px; color: #F8FAFC;">
                    Symbolic AI vs. Statistical Learning: Why expert systems lost and neural networks won.
                  </div>
                </div>
                """
            }
        ]

        return self.render_slides(day=1, topic="What is Artificial Intelligence?", slides_data=slides)

if __name__ == "__main__":
    generator = InstagramCarouselGenerator()
    paths = generator.build_day1_sample()
    print(f"Generated {len(paths)} enlarged enriched slides successfully!")
