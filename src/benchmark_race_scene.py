import os
import json
try:
    from manim import *
except ImportError:
    class Scene:
        pass

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


class BenchmarkRace(Scene):
    def construct(self):
        self.camera.background_color = BG_COLOR
        spec = get_spec()

        title_text = spec.get("title", "AI INFERENCE BENCHMARK RACE").upper()[:36]
        subtitle_text = spec.get("subtitle", "Measured Real-Time Tokens Per Second (TPS) and Latency")[:60]
        raw_models = spec.get("models", [])
        if not raw_models:
            raw_models = [
                {"name": "DeepSeek R1", "tps": 135, "ttft": "160ms"},
                {"name": "Claude 3.5 Sonnet", "tps": 110, "ttft": "220ms"},
                {"name": "Llama 3.3 70B", "tps": 88, "ttft": "290ms"},
            ]

        # Top Tag / Badge
        badge_box = RoundedRectangle(corner_radius=0.1, width=3.4, height=0.5, color=BORDER_COLOR, fill_color="#1e293b", fill_opacity=0.9)
        badge_text = Text("⚡ NEUBENCH BENCHMARK", font_size=18, color=CYAN_ACCENT, weight=BOLD)
        badge = VGroup(badge_box, badge_text).to_corner(UL, buff=0.8)

        # Title & Subtitle
        title = Text(title_text, font_size=32, color=WHITE, weight=BOLD).next_to(badge, DOWN, aligned_edge=LEFT, buff=0.25)
        subtitle = Text(subtitle_text, font_size=18, color=MUTED).next_to(title, DOWN, aligned_edge=LEFT, buff=0.15)

        header = VGroup(badge, title, subtitle)

        # Footer
        footer_line = Line(start=[-6.2, -5.8, 0], end=[6.2, -5.8, 0], color=BORDER_COLOR, stroke_width=1.5)
        footer_text1 = Text("NeuBench Automated Runner", font_size=16, color=MUTED).next_to(footer_line, DOWN, aligned_edge=LEFT, buff=0.2)
        footer_text2 = Text("app.neubench.workers.dev", font_size=16, color=CYAN_ACCENT, weight=BOLD).next_to(footer_line, DOWN, aligned_edge=RIGHT, buff=0.2)
        footer = VGroup(footer_line, footer_text1, footer_text2)

        # Models Bar Chart
        colors = [CYAN_ACCENT, EMERALD_ACCENT, AMBER_ACCENT, PURPLE_ACCENT, PINK_ACCENT]
        models = raw_models[:5]
        max_tps = max([float(m.get("tps", 100)) for m in models] or [100.0])

        rows = []
        bar_animations = []

        start_y = 1.6
        y_gap = 1.45

        for i, m in enumerate(models):
            y_pos = start_y - (i * y_gap)
            m_name = str(m.get("name", f"Model {i+1}"))[:20]
            m_tps = int(m.get("tps", 80))
            m_ttft = str(m.get("ttft", "200ms"))
            color = colors[i % len(colors)]

            # Label (Name + TTFT)
            name_lbl = Text(m_name, font_size=20, color=WHITE, weight=BOLD)
            ttft_lbl = Text(f"TTFT: {m_ttft}", font_size=14, color=MUTED)
            lbl_group = VGroup(name_lbl, ttft_lbl).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
            lbl_group.move_to([-4.8, y_pos, 0], aligned_edge=LEFT)

            # Track
            track_w = 6.2
            track_h = 0.55
            track = RoundedRectangle(
                corner_radius=0.12,
                width=track_w,
                height=track_h,
                color="#0f172a",
                fill_color="#0f172a",
                fill_opacity=0.9,
                stroke_width=1
            )
            track.move_to([-1.0, y_pos, 0], aligned_edge=LEFT)

            # Bar
            bar_pct = max(0.08, min(1.0, m_tps / max_tps))
            bar_w = track_w * bar_pct
            bar = RoundedRectangle(
                corner_radius=0.12,
                width=bar_w,
                height=track_h,
                color=color,
                fill_color=color,
                fill_opacity=0.95,
                stroke_width=0
            )
            bar.move_to([-1.0, y_pos, 0], aligned_edge=LEFT)

            # TPS value text
            tps_lbl = Text(f"{m_tps} tps", font_size=20, color=color, weight=BOLD)
            tps_lbl.next_to(track, RIGHT, buff=0.25)

            rows.append(VGroup(lbl_group, track, tps_lbl))
            bar_animations.append(GrowFromEdge(bar, LEFT))

        # Frame 0 must be fully populated with layout and text so social thumbnails are never black
        self.add(header, footer)
        for r in rows:
            self.add(r)
        self.play(*bar_animations, run_time=1.5)
        self.wait(1.5)
