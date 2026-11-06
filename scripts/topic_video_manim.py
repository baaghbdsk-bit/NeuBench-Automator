from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

from manim import *

CREAM = "#F4F0E6"
PAPER = "#FFFDF8"
INK = "#141414"
MUTED = "#666158"
ACCENT = "#E4572E"
TEAL = "#1D7874"
PALE = "#DDD5C6"

DISPLAY_FONT = os.getenv("TOPIC_VIDEO_DISPLAY_FONT", "Bahnschrift")
BODY_FONT = os.getenv("TOPIC_VIDEO_BODY_FONT", "Segoe UI")

SPEC_PATH = Path(os.environ["TOPIC_VIDEO_SPEC"]).resolve()
SPEC_DIR = SPEC_PATH.parent
SPEC = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
SECTIONS = SPEC["sections"]
TOTAL = len(SECTIONS)
MEDIA_DIR = Path(os.environ.get("TOPIC_VIDEO_MEDIA_DIR", SPEC_DIR / "render")).resolve()

config.background_color = CREAM
config.frame_width = 9
config.frame_height = 16
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_rate = 30
config.media_dir = str(MEDIA_DIR)
config.output_file = SPEC["slug"]


def load_timings() -> list[float]:
    path = SPEC_DIR / "timings.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        durations = [float(x) for x in data["durations"]]
        if len(durations) == TOTAL:
            return durations
    return [8.0] * TOTAL


T = load_timings()


def txt(
    s: str,
    size: float = 30,
    color: str = INK,
    font: str = BODY_FONT,
    weight: str = "NORMAL",
    **kwargs,
) -> Text:
    return Text(s, font=font, font_size=size, color=color, weight=weight, **kwargs)


def text_block(
    s: str,
    size: float = 30,
    color: str = INK,
    font: str = BODY_FONT,
    weight: str = "NORMAL",
    max_chars: int = 32,
    line_spacing: float = 0.65,
) -> Text:
    lines = textwrap.wrap(s.strip(), width=max_chars) or [""]
    return Text(
        "\n".join(lines),
        font=font,
        font_size=size,
        color=color,
        weight=weight,
        line_spacing=line_spacing,
    )


def section_header(number: int, label: str) -> VGroup:
    brand = txt("PLAIN AI", 19, INK, DISPLAY_FONT, "BOLD")
    brand.move_to([-3.55, 7.25, 0], aligned_edge=LEFT)
    count = txt(f"{number:02d} / {TOTAL:02d}", 18, MUTED, BODY_FONT, "BOLD")
    count.move_to([3.55, 7.25, 0], aligned_edge=RIGHT)
    rule = Line([-3.9, 6.78, 0], [3.9, 6.78, 0], color=INK, stroke_width=2)
    kicker = txt(label.upper(), 15, ACCENT, BODY_FONT, "BOLD")
    kicker.next_to(rule, DOWN, buff=0.18).align_to(rule, LEFT)
    return VGroup(brand, count, rule, kicker)


def progress_bar(progress: Mobject, index: int) -> Mobject:
    target = Rectangle(
        width=7.8 * (index / TOTAL),
        height=0.055,
        stroke_width=0,
        fill_color=ACCENT,
        fill_opacity=1,
    )
    target.align_to(progress.get_left(), LEFT)
    target.set_y(progress.get_y())
    return target


def fit(mobject: Mobject, width: float = 8.2, height: float = 9.0) -> Mobject:
    if mobject.width > width:
        mobject.scale_to_fit_width(width)
    if mobject.height > height:
        mobject.scale_to_fit_height(height)
    return mobject


def content_frame(*mobjects: Mobject) -> VGroup:
    group = VGroup(*mobjects)
    fit(group)
    group.move_to([0, 0.55, 0])
    return group


class TopicVideo(Scene):
    def construct(self):
        durations = T
        track = Rectangle(
            width=7.8, height=0.055, stroke_width=0, fill_color=PALE, fill_opacity=1
        ).set_y(6.42)
        progress = Rectangle(
            width=0.001, height=0.055, stroke_width=0, fill_color=ACCENT, fill_opacity=1
        )
        progress.align_to(track, LEFT).set_y(track.get_y())
        self.add(track, progress)
        self.add(section_header(1, SECTIONS[0].get("kicker", "")))

        for i, (section, duration) in enumerate(zip(SECTIONS, durations), 1):
            start = self.renderer.time
            self.play(Transform(progress, progress_bar(progress, i)), run_time=0.2)
            content = self.render_section(section)
            self.play(FadeIn(content, shift=UP * 0.18), run_time=0.7)
            self.wait_until(start + duration - 0.35)
            self.play(FadeOut(content), run_time=0.35)
            if i < TOTAL:
                self.clear()
                self.add(track, progress)
                self.add(section_header(i + 1, SECTIONS[i].get("kicker", "")))

    def wait_until(self, target: float) -> None:
        remaining = target - self.renderer.time
        if remaining > 0:
            self.wait(remaining)

    def render_section(self, section: dict) -> VGroup:
        kind = section.get("kind", "statement")
        if kind == "cover":
            return self.render_cover(section)
        if kind == "compare":
            return self.render_compare(section)
        if kind == "steps":
            return self.render_steps(section)
        if kind == "quote":
            return self.render_quote(section)
        if kind == "recap":
            return self.render_recap(section)
        return self.render_statement(section)

    def render_cover(self, section: dict) -> VGroup:
        heading = text_block(
            section.get("heading", ""),
            size=58,
            color=INK,
            font=DISPLAY_FONT,
            weight="BOLD",
            max_chars=18,
            line_spacing=0.9,
        )
        body = text_block(
            section.get("body", ""),
            size=32,
            color=ACCENT,
            font=DISPLAY_FONT,
            weight="BOLD",
            max_chars=28,
        )
        rule = Line([-3.9, 0, 0], [-1.4, 0, 0], color=ACCENT, stroke_width=7)
        group = VGroup(heading, rule, body).arrange(DOWN, buff=0.38, aligned_edge=LEFT)
        group.move_to([0, 0.7, 0])
        fit(group)
        return group

    def render_statement(self, section: dict) -> VGroup:
        heading = text_block(
            section.get("heading", ""),
            size=40,
            color=INK,
            font=DISPLAY_FONT,
            weight="BOLD",
            max_chars=28,
        )
        body = text_block(
            section.get("body", ""),
            size=30,
            color=INK,
            font=BODY_FONT,
            max_chars=34,
            line_spacing=0.75,
        )
        rule = Line([0, 0, 0], [1.35, 0, 0], color=ACCENT, stroke_width=6)
        group = VGroup(heading, rule, body).arrange(DOWN, buff=0.34, aligned_edge=LEFT)
        group.move_to([-3.8, 0.7, 0], aligned_edge=LEFT)
        fit(group)
        return group

    def render_compare(self, section: dict) -> VGroup:
        heading = text_block(
            section.get("heading", ""),
            size=38,
            color=INK,
            font=DISPLAY_FONT,
            weight="BOLD",
            max_chars=28,
        )
        left = VGroup(
            txt(section.get("left_title", "WITHOUT IT").upper(), 18, TEAL, BODY_FONT, "BOLD"),
            text_block(section.get("left_body", ""), 27, INK, max_chars=22),
        ).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        right = VGroup(
            txt(section.get("right_title", "WITH IT").upper(), 18, ACCENT, BODY_FONT, "BOLD"),
            text_block(section.get("right_body", ""), 27, INK, max_chars=22),
        ).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        columns = VGroup(left, right).arrange(RIGHT, buff=1.15, aligned_edge=UP)
        group = VGroup(heading, columns).arrange(DOWN, buff=0.55)
        group.move_to([0, 0.6, 0])
        fit(group)
        divider = Line(
            [columns.get_center()[0], columns.get_top()[1] + 0.1, 0],
            [columns.get_center()[0], columns.get_bottom()[1] - 0.1, 0],
            color=PALE,
            stroke_width=2,
        )
        group.add(divider)
        return group

    def render_steps(self, section: dict) -> VGroup:
        heading = text_block(
            section.get("heading", ""),
            size=38,
            color=INK,
            font=DISPLAY_FONT,
            weight="BOLD",
            max_chars=28,
        )
        rows = VGroup()
        for index, item in enumerate(section.get("items", [])[:3], 1):
            number = txt(f"{index:02d}", 30, ACCENT, DISPLAY_FONT, "BOLD")
            body = text_block(item, 25, INK, max_chars=34, line_spacing=0.7)
            row = VGroup(number, body).arrange(RIGHT, buff=0.35, aligned_edge=UP)
            rows.add(row)
        rows.arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        group = VGroup(heading, rows).arrange(DOWN, buff=0.55, aligned_edge=LEFT)
        group.move_to([-3.8, 0.7, 0], aligned_edge=LEFT)
        fit(group)
        return group

    def render_quote(self, section: dict) -> VGroup:
        heading = txt(section.get("heading", "").upper(), 18, ACCENT, BODY_FONT, "BOLD")
        body = text_block(
            section.get("body", ""),
            size=38,
            color=INK,
            font=DISPLAY_FONT,
            weight="BOLD",
            max_chars=26,
            line_spacing=0.85,
        )
        bar = Line([0, 0, 0], [0, 2.6, 0], color=ACCENT, stroke_width=8)
        text_group = VGroup(heading, body).arrange(DOWN, buff=0.38, aligned_edge=LEFT)
        group = VGroup(bar, text_group).arrange(RIGHT, buff=0.45, aligned_edge=UP)
        group.move_to([0, 0.7, 0])
        fit(group)
        return group

    def render_recap(self, section: dict) -> VGroup:
        heading = text_block(
            section.get("heading", ""),
            size=40,
            color=INK,
            font=DISPLAY_FONT,
            weight="BOLD",
            max_chars=28,
        )
        rows = VGroup()
        for item in section.get("items", [])[:3]:
            mark = Line([0, 0, 0], [0.45, 0, 0], color=ACCENT, stroke_width=6)
            body = text_block(item, 26, INK, max_chars=36, line_spacing=0.7)
            row = VGroup(mark, body).arrange(RIGHT, buff=0.3, aligned_edge=UP)
            rows.add(row)
        rows.arrange(DOWN, buff=0.4, aligned_edge=LEFT)
        group = VGroup(heading, rows).arrange(DOWN, buff=0.6, aligned_edge=LEFT)
        group.move_to([-3.8, 0.8, 0], aligned_edge=LEFT)
        fit(group)
        return group
