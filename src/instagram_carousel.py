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
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
  
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  
  body {{
    width: 1080px;
    height: 1350px;
    background: #090D16;
    color: #F8FAFC;
    font-family: 'Plus Jakarta Sans', sans-serif;
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 90px 80px 70px 80px;
  }}
  
  .glow-top {{
    position: absolute;
    top: -150px;
    right: -100px;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.18) 0%, rgba(99, 102, 241, 0) 70%);
    pointer-events: none;
  }}
  
  .glow-bottom {{
    position: absolute;
    bottom: -150px;
    left: -100px;
    width: 550px;
    height: 550px;
    background: radial-gradient(circle, rgba(168, 85, 247, 0.15) 0%, rgba(168, 85, 247, 0) 70%);
    pointer-events: none;
  }}

  .header-badge {{
    display: inline-flex;
    align-items: center;
    gap: 12px;
    padding: 10px 22px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 999px;
    font-size: 20px;
    font-weight: 700;
    color: #818CF8;
    text-transform: uppercase;
    letter-spacing: 2px;
  }}

  .slide-counter {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 22px;
    color: #64748B;
    font-weight: 700;
  }}

  .top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 10;
  }}

  .main-content {{
    display: flex;
    flex-direction: column;
    gap: 36px;
    z-index: 10;
    flex-grow: 1;
    justify-content: center;
  }}

  .title-tag {{
    font-size: 24px;
    color: #A855F7;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
  }}

  .hero-title {{
    font-size: 58px;
    line-height: 1.15;
    font-weight: 800;
    letter-spacing: -1.5px;
    background: linear-gradient(135deg, #FFFFFF 0%, #CBD5E1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}

  .hero-body {{
    font-size: 30px;
    line-height: 1.5;
    color: #94A3B8;
    font-weight: 400;
  }}

  .info-card {{
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 28px;
    padding: 40px;
    box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(20px);
  }}

  .card-title {{
    font-size: 26px;
    font-weight: 700;
    color: #38BDF8;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 14px;
  }}

  .card-body {{
    font-size: 27px;
    line-height: 1.55;
    color: #E2E8F0;
  }}

  .code-block {{
    background: #020617;
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 20px;
    padding: 30px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 23px;
    line-height: 1.6;
    color: #38BDF8;
  }}

  .bullet-list {{
    display: flex;
    flex-direction: column;
    gap: 22px;
  }}

  .bullet-item {{
    display: flex;
    gap: 18px;
    font-size: 28px;
    line-height: 1.45;
    color: #CBD5E1;
  }}

  .bullet-icon {{
    color: #818CF8;
    font-weight: 800;
  }}

  .footer-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 35px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    z-index: 10;
  }}

  .author-info {{
    display: flex;
    align-items: center;
    gap: 16px;
  }}

  .author-avatar {{
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366F1, #A855F7);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    font-weight: 800;
    color: #FFF;
  }}

  .author-meta {{
    display: flex;
    flex-direction: column;
  }}

  .author-name {{
    font-size: 22px;
    font-weight: 700;
    color: #F8FAFC;
  }}

  .author-handle {{
    font-size: 18px;
    color: #64748B;
  }}

  .brand-badge {{
    font-size: 20px;
    font-weight: 700;
    color: #818CF8;
    background: rgba(99, 102, 241, 0.1);
    padding: 8px 20px;
    border-radius: 999px;
    border: 1px solid rgba(99, 102, 241, 0.2);
  }}
</style>
</head>
<body>
  <div class="glow-top"></div>
  <div class="glow-bottom"></div>

  <!-- Top bar -->
  <div class="top-bar">
    <div class="header-badge">{series_title}</div>
    <div class="slide-counter">{current_slide} / {total_slides}</div>
  </div>

  <!-- Main Content -->
  <div class="main-content">
    {content_html}
  </div>

  <!-- Footer -->
  <div class="footer-bar">
    <div class="author-info">
      <div class="author-avatar">VG</div>
      <div class="author-meta">
        <span class="author-name">Vishnu Gupta</span>
        <span class="author-handle">@neubench • AI Master Series</span>
      </div>
    </div>
    <div class="brand-badge">neubench.netlify.app</div>
  </div>
</body>
</html>
"""

class InstagramCarouselGenerator:
    """Generates high-aesthetic 1080x1350 carousel PNG slides from lesson markdown."""

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
                full_html = HTML_TEMPLATE.format(
                    series_title=f"AI Masterclass • Day {day:02d}",
                    current_slide=f"{idx:02d}",
                    total_slides=f"{total_slides:02d}",
                    content_html=slide["html"]
                )

                page.set_content(full_html, wait_until="networkidle")
                output_path = day_dir / f"slide_{idx:02d}.png"
                page.screenshot(path=str(output_path), type="png")
                generated_files.append(str(output_path))
                print(f"[InstagramCarousel] ✅ Rendered: {output_path.name}")

            browser.close()

        return generated_files

    def build_day1_sample(self) -> List[str]:
        """Constructs and renders the 5 high-converting slides for Day 1."""
        slides = [
            # Slide 1: Cover / Hook
            {
                "html": """
                <div class="title-tag">Day 01 of 90 • Core Mental Model</div>
                <h1 class="hero-title">What is Artificial Intelligence?</h1>
                <p class="hero-body">Why writing thousands of if-else statements is failing—and how learned behavior changes modern software forever.</p>
                <div class="info-card">
                  <div class="card-title">💡 The Shift in 1 Line</div>
                  <div class="card-body">Traditional programming creates the rules. <strong>Machine Learning learns the rules from data.</strong></div>
                </div>
                """
            },
            # Slide 2: Rules vs Learned Architecture
            {
                "html": """
                <div class="title-tag">The Fundamental Paradigm</div>
                <h1 class="hero-title" style="font-size: 46px;">Rules-Based Code vs. Machine Learning</h1>
                <div class="info-card">
                  <div class="card-title">⚙️ Traditional Programming</div>
                  <div class="code-block" style="color: #94A3B8;">
                    Data + Rules ──► Computer ──► Answers
                  </div>
                </div>
                <div class="info-card">
                  <div class="card-title">🧠 Machine Learning (AI)</div>
                  <div class="code-block" style="color: #38BDF8;">
                    Data + Answers ──► Computer ──► Learned Rules
                  </div>
                </div>
                """
            },
            # Slide 3: Real World Scenario (QA / Automation)
            {
                "html": """
                <div class="title-tag">Real-World Engineering</div>
                <h1 class="hero-title" style="font-size: 46px;">Why This Matters in Software</h1>
                <div class="bullet-list">
                  <div class="bullet-item">
                    <span class="bullet-icon">❌</span>
                    <span><strong>Brittle Rules:</strong> A QA test searching for <code>#submit-btn-v2</code> breaks immediately when a frontend dev renames the ID.</span>
                  </div>
                  <div class="bullet-item">
                    <span class="bullet-icon">✅</span>
                    <span><strong>AI Perception:</strong> Visual AI models detect the button context semantically. The ID can change, and the test still passes.</span>
                  </div>
                </div>
                <div class="info-card" style="margin-top: 10px;">
                  <div class="card-body" style="font-size: 24px; color: #CBD5E1;">
                    Rules scale linearly with engineer burnout.<br>
                    <strong>AI models scale dynamically with data.</strong>
                  </div>
                </div>
                """
            },
            # Slide 4: 3 Golden Takeaways
            {
                "html": """
                <div class="title-tag">Core Principles</div>
                <h1 class="hero-title" style="font-size: 48px;">3 Golden Takeaways</h1>
                <div class="bullet-list">
                  <div class="bullet-item">
                    <span class="bullet-icon">1.</span>
                    <span><strong>Deterministic vs. Probabilistic:</strong> Traditional code always gives exact results; AI predicts patterns based on probability.</span>
                  </div>
                  <div class="bullet-item">
                    <span class="bullet-icon">2.</span>
                    <span><strong>Data is the Source Code:</strong> In AI, bad data produces bad logic. Data quality always trumps parameter count.</span>
                  </div>
                  <div class="bullet-item">
                    <span class="bullet-icon">3.</span>
                    <span><strong>The Coexistence Rule:</strong> AI doesn't replace code. We use code for precise logic and AI for human perception.</span>
                  </div>
                </div>
                """
            },
            # Slide 5: Call to Action / Retention
            {
                "html": """
                <div class="title-tag">Complete 90-Day Curriculum</div>
                <h1 class="hero-title" style="font-size: 52px;">Follow the 90-Day AI Journey</h1>
                <p class="hero-body">Tomorrow we unlock <strong>Day 02: AI vs. Machine Learning vs. Deep Learning</strong> (The nested mental model).</p>
                <div class="info-card" style="border: 1px solid rgba(129, 140, 248, 0.4); background: rgba(99, 102, 241, 0.08);">
                  <div class="card-title">📌 Save this post for your revision!</div>
                  <div class="card-body" style="font-size: 24px;">
                    Drop a comment below with <strong>"AI90"</strong> and I'll send you the complete curriculum roadmap with GitHub references.
                  </div>
                </div>
                """
            }
        ]

        return self.render_slides(day=1, topic="What is Artificial Intelligence?", slides_data=slides)

if __name__ == "__main__":
    generator = InstagramCarouselGenerator()
    paths = generator.build_day1_sample()
    print(f"Generated {len(paths)} slides successfully!")
