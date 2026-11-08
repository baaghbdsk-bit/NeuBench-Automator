import os
import json
from manim import *

# NeuBench Theme Palette
BG_COLOR = "#0a0e17"       # Deep Midnight Blue
CARD_BG = "#111827"        # Slate Card
BORDER_COLOR = "#1e293b"   # Slate Border
CYAN_ACCENT = "#38bdf8"    # Electric Cyan
AMBER_ACCENT = "#fbbf24"   # Warm Amber
EMERALD_ACCENT = "#34d399" # Emerald Green
PURPLE_ACCENT = "#c084fc"  # Tech Purple
PINK_ACCENT = "#f472b6"    # Pink Accent
WHITE = "#f8fafc"
MUTED = "#94a3b8"
MUTED_DARK = "#64748b"


def get_spec() -> dict:
    spec_path = os.environ.get("MANIM_SPEC_PATH")
    if spec_path and os.path.exists(spec_path):
        try:
            with open(spec_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and data.get("title"):
                    return data
        except Exception as e:
            raise RuntimeError(f"Failed to load dynamic spec from MANIM_SPEC_PATH ({spec_path}): {e}")
    raise RuntimeError(
        "No dynamic topic spec provided via MANIM_SPEC_PATH. "
        "Static fallback is disabled to prevent repeating off-topic looping GIFs."
    )


class TokenPipeline(Scene):
    def construct(self):
        self.camera.background_color = BG_COLOR
        spec = get_spec()

        title_text = spec.get("title", "HOW LLMS READ YOUR PROMPT").upper()[:36]
        subtitle_text = spec.get("subtitle", "Subword Tokenization to High-Dimensional Embeddings")[:60]
        prompt_text = spec.get("prompt_string", "Why is latency high in multi-agent workflows?")[:50]
        raw_tokens = spec.get("tokens", [])
        if not raw_tokens:
            raw_tokens = [
                {"text": "Why", "id": 14235},
                {"text": "is", "id": 374},
                {"text": "latency", "id": 21904},
                {"text": "high", "id": 1024},
                {"text": "agents", "id": 45192},
            ]

        # Top Badge
        badge_box = RoundedRectangle(corner_radius=0.1, width=3.2, height=0.5, color=BORDER_COLOR, fill_color="#1e293b", fill_opacity=0.9)
        badge_text = Text("⚡ NEUBENCH ARCH", font_size=18, color=CYAN_ACCENT, weight=BOLD)
        badge = VGroup(badge_box, badge_text).to_corner(UL, buff=0.8)

        # Title & Subtitle
        title = Text(title_text, font_size=30, color=WHITE, weight=BOLD).next_to(badge, DOWN, aligned_edge=LEFT, buff=0.22)
        subtitle = Text(subtitle_text, font_size=17, color=MUTED).next_to(title, DOWN, aligned_edge=LEFT, buff=0.14)
        header = VGroup(badge, title, subtitle)

        # Footer
        footer_line = Line(start=[-6.2, -5.8, 0], end=[6.2, -5.8, 0], color=BORDER_COLOR, stroke_width=1.5)
        footer_text1 = Text("NeuBench Research — Continuous AI LLM Benchmarking", font_size=16, color=MUTED).next_to(footer_line, DOWN, aligned_edge=LEFT, buff=0.2)
        footer_text2 = Text("app.neubench.workers.dev", font_size=16, color=CYAN_ACCENT, weight=BOLD).next_to(footer_line, DOWN, aligned_edge=RIGHT, buff=0.2)
        footer = VGroup(footer_line, footer_text1, footer_text2)

        card_w = 11.8

        # Step 1: Raw Prompt Card
        s1_box = RoundedRectangle(corner_radius=0.12, width=card_w, height=1.35, color=BORDER_COLOR, fill_color=CARD_BG, fill_opacity=0.95, stroke_width=1.5)
        s1_title = Text("STEP 1: RAW STRING PROMPT", font_size=15, color=CYAN_ACCENT, weight=BOLD)
        s1_prompt = Text(f'"{prompt_text}"', font_size=17, color=WHITE, font="Consolas")
        s1_content = VGroup(s1_title, s1_prompt).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to(s1_box.get_center())
        step1 = VGroup(s1_box, s1_content).move_to([0, 1.8, 0])

        # Arrow 1
        arrow1 = Arrow(start=[0, 1.05, 0], end=[0, 0.65, 0], color=CYAN_ACCENT, stroke_width=3, buff=0.05, max_tip_length_to_length_ratio=0.3)

        # Step 2: BPE Subwords / Token IDs
        s2_box = RoundedRectangle(corner_radius=0.12, width=card_w, height=1.8, color=BORDER_COLOR, fill_color=CARD_BG, fill_opacity=0.95, stroke_width=1.5)
        s2_title = Text("STEP 2: BYTE-PAIR ENCODING (TOKEN IDS)", font_size=15, color=AMBER_ACCENT, weight=BOLD)
        s2_title.move_to(s2_box.get_top() + DOWN * 0.35).align_to(s1_title, LEFT)

        colors = [CYAN_ACCENT, AMBER_ACCENT, EMERALD_ACCENT, PURPLE_ACCENT, PINK_ACCENT]
        token_badges = VGroup()
        for idx, t in enumerate(raw_tokens[:6]):
            tok_text = str(t.get("text", f"tok{idx}"))[:12]
            tok_id = int(t.get("id", 1000 + idx))
            col = colors[idx % len(colors)]

            badge_w = max(1.4, len(tok_text) * 0.18 + 0.5)
            b_rect = RoundedRectangle(corner_radius=0.08, width=badge_w, height=0.75, color=col, fill_color="#0f172a", fill_opacity=0.95, stroke_width=1.5)
            t_txt = Text(tok_text, font_size=14, color=WHITE, font="Consolas")
            i_txt = Text(f"#{tok_id}", font_size=12, color=col, font="Consolas")
            b_cnt = VGroup(t_txt, i_txt).arrange(DOWN, buff=0.06).move_to(b_rect.get_center())
            token_badges.add(VGroup(b_rect, b_cnt))

        token_badges.arrange(RIGHT, buff=0.25).move_to(s2_box.get_bottom() + UP * 0.55)
        step2 = VGroup(s2_box, s2_title, token_badges).move_to([0, -0.3, 0])

        # Arrow 2
        arrow2 = Arrow(start=[0, -1.25, 0], end=[0, -1.65, 0], color=AMBER_ACCENT, stroke_width=3, buff=0.05, max_tip_length_to_length_ratio=0.3)

        # Step 3: Embeddings
        s3_box = RoundedRectangle(corner_radius=0.12, width=card_w, height=2.4, color=BORDER_COLOR, fill_color=CARD_BG, fill_opacity=0.95, stroke_width=1.5)
        s3_title = Text("STEP 3: EMBEDDING LOOKUP MATRIX (D = 4,096)", font_size=15, color=EMERALD_ACCENT, weight=BOLD)
        s3_title.move_to(s3_box.get_top() + DOWN * 0.35).align_to(s1_title, LEFT)

        matrix_rows = VGroup()
        for idx, t in enumerate(raw_tokens[:4]):
            tok_text = str(t.get("text", f"tok{idx}"))[:8]
            col = colors[idx % len(colors)]
            row_txt = Text(f"{tok_text:>8}  ->  [ +0.84,  -0.62,  +0.91,  ...  +0.18 ] in R^4096", font_size=14, color=col, font="Consolas")
            matrix_rows.add(row_txt)

        matrix_rows.arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        matrix_rows.next_to(s3_title, DOWN, buff=0.25).align_to(s3_title, LEFT)
        step3 = VGroup(s3_box, s3_title, matrix_rows).move_to([0, -3.1, 0])

        # Frame 0 must be fully populated with layout and text so social thumbnails are never black
        self.add(header, footer, step1, arrow1, step2, arrow2, s3_box, s3_title)
        self.play(Write(matrix_rows), run_time=1.5)
        self.play(Indicate(token_badges, color=CYAN_ACCENT, scale_factor=1.05), run_time=0.8)
        self.wait(1.5)
