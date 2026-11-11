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


class CodeArchitecture(Scene):
    def construct(self):
        self.camera.background_color = BG_COLOR
        spec = get_spec()

        title_text = spec.get("title", "SYSTEM ARCHITECTURE BLUEPRINT").upper()[:36]
        subtitle_text = spec.get("subtitle", "Continuous AI Architecture Series")[:60]
        box1_title = spec.get("box1_title", "INGESTION & PREFILL")[:22]
        box1_desc = spec.get("box1_desc", "Parallel KV prefill")[:32]
        box1_stat = spec.get("box1_stat", "Sub-millisecond latency")[:32]
        arrow_label = spec.get("arrow_label", "High-speed bus")[:16]
        box2_title = spec.get("box2_title", "EXECUTION & DECODE")[:22]
        box2_desc = spec.get("box2_desc", "Autoregressive decode")[:32]
        box2_stat = spec.get("box2_stat", "Zero memory waste")[:32]
        code_filename = spec.get("code_filename", "architecture.py")[:24]
        raw_code = spec.get("code_lines", ["# Execution pipeline", "result = model.run(data)"])
        impact_badge = spec.get("impact_badge", "⚡ SYSTEM IMPACT: Optimized throughput with zero bottlenecks")[:65]

        # Top Badge
        badge_box = RoundedRectangle(corner_radius=0.1, width=3.2, height=0.5, color=BORDER_COLOR, fill_color="#1e293b", fill_opacity=0.9)
        badge_text = Text("⚡ NEUBENCH BLUEPRINT", font_size=18, color=CYAN_ACCENT, weight=BOLD)
        badge = VGroup(badge_box, badge_text).to_corner(UL, buff=0.8)

        # Title & Subtitle
        title = Text(title_text, font_size=30, color=WHITE, weight=BOLD).next_to(badge, DOWN, aligned_edge=LEFT, buff=0.22)
        subtitle = Text(subtitle_text, font_size=17, color=MUTED).next_to(title, DOWN, aligned_edge=LEFT, buff=0.14)
        header = VGroup(badge, title, subtitle)

        # Flow Boxes
        # Box 1
        box1_bg = RoundedRectangle(corner_radius=0.15, width=4.8, height=1.6, color=CYAN_ACCENT, fill_color=CARD_BG, fill_opacity=0.95, stroke_width=2)
        t1 = Text(box1_title, font_size=18, color=CYAN_ACCENT, weight=BOLD)
        d1 = Text(box1_desc, font_size=14, color=MUTED)
        s1 = Text(box1_stat, font_size=13, color=WHITE)
        b1_content = VGroup(t1, d1, s1).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to(box1_bg.get_center())
        box1 = VGroup(box1_bg, b1_content).move_to([-3.4, 1.4, 0])

        # Box 2
        box2_bg = RoundedRectangle(corner_radius=0.15, width=4.8, height=1.6, color=EMERALD_ACCENT, fill_color=CARD_BG, fill_opacity=0.95, stroke_width=2)
        t2 = Text(box2_title, font_size=18, color=EMERALD_ACCENT, weight=BOLD)
        d2 = Text(box2_desc, font_size=14, color=MUTED)
        s2 = Text(box2_stat, font_size=13, color=WHITE)
        b2_content = VGroup(t2, d2, s2).arrange(DOWN, aligned_edge=LEFT, buff=0.12).move_to(box2_bg.get_center())
        box2 = VGroup(box2_bg, b2_content).move_to([3.4, 1.4, 0])

        # Arrow between Box 1 and Box 2
        arrow = Arrow(start=box1.get_right() + RIGHT * 0.1, end=box2.get_left() + LEFT * 0.1, color=AMBER_ACCENT, buff=0.1, stroke_width=3, max_tip_length_to_length_ratio=0.25)
        arrow_lbl = Text(arrow_label, font_size=13, color=AMBER_ACCENT, weight=BOLD).next_to(arrow, UP, buff=0.08)
        flow_arrow = VGroup(arrow, arrow_lbl)

        # IDE Window Card
        ide_w, ide_h = 11.6, 4.2
        ide_bg = RoundedRectangle(corner_radius=0.15, width=ide_w, height=ide_h, color=BORDER_COLOR, fill_color="#0d1117", fill_opacity=0.98, stroke_width=2)
        ide_bg.move_to([0, -2.0, 0])

        # IDE Header bar
        header_bar = RoundedRectangle(corner_radius=0.12, width=ide_w, height=0.6, color=BORDER_COLOR, fill_color="#161b22", fill_opacity=1.0, stroke_width=1)
        header_bar.move_to(ide_bg.get_top() + DOWN * 0.3)

        dot_r = Dot(radius=0.08, color="#ef4444").move_to(header_bar.get_left() + RIGHT * 0.35)
        dot_y = Dot(radius=0.08, color="#f59e0b").next_to(dot_r, RIGHT, buff=0.15)
        dot_g = Dot(radius=0.08, color="#22c55e").next_to(dot_y, RIGHT, buff=0.15)
        ide_title = Text(f"{code_filename} — NeuBench Architecture", font_size=14, color=MUTED).next_to(dot_g, RIGHT, buff=0.4)
        ide_top = VGroup(header_bar, dot_r, dot_y, dot_g, ide_title)

        # Code lines
        code_colors = [CYAN_ACCENT, AMBER_ACCENT, EMERALD_ACCENT, PURPLE_ACCENT, PINK_ACCENT]
        code_vgroup = VGroup()
        for idx, line in enumerate(raw_code[:5]):
            line_str = str(line)
            c = MUTED if line_str.strip().startswith("#") else code_colors[idx % len(code_colors)]
            num_t = Text(f"{idx+1:2d}", font_size=14, color=MUTED_DARK, font="Consolas")
            code_t = Text(line_str[:54], font_size=15, color=c, font="Consolas")
            row = VGroup(num_t, code_t).arrange(RIGHT, buff=0.3, aligned_edge=DOWN)
            code_vgroup.add(row)
        code_vgroup.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        code_vgroup.next_to(header_bar, DOWN, buff=0.35).align_to(header_bar, LEFT).shift(RIGHT * 0.4)

        # Impact Badge
        badge_rect = RoundedRectangle(corner_radius=0.1, width=ide_w - 0.8, height=0.55, color=PURPLE_ACCENT, fill_color="#0f172a", fill_opacity=0.9, stroke_width=1.5)
        badge_t = Text(impact_badge, font_size=14, color=WHITE, weight=BOLD)
        impact_grp = VGroup(badge_rect, badge_t).move_to(ide_bg.get_bottom() + UP * 0.45)

        ide_window = VGroup(ide_bg, ide_top, code_vgroup, impact_grp)

        # Footer
        footer_line = Line(start=[-6.2, -5.8, 0], end=[6.2, -5.8, 0], color=BORDER_COLOR, stroke_width=1.5)
        footer_text1 = Text("NeuBench Engineering Architecture Series", font_size=16, color=MUTED).next_to(footer_line, DOWN, aligned_edge=LEFT, buff=0.2)
        footer_text2 = Text("app.neubench.workers.dev", font_size=16, color=CYAN_ACCENT, weight=BOLD).next_to(footer_line, DOWN, aligned_edge=RIGHT, buff=0.2)
        footer = VGroup(footer_line, footer_text1, footer_text2)

        # Frame 0 must be fully populated with layout and text so social thumbnails are never black
        self.add(header, footer, box1, box2, flow_arrow, ide_bg, ide_top, impact_grp)
        self.play(Write(code_vgroup), run_time=1.5)
        self.play(Indicate(flow_arrow, color=AMBER_ACCENT, scale_factor=1.05), run_time=0.8)
        self.wait(1.5)
