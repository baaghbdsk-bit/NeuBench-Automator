import json
import re
from pathlib import Path
from typing import Optional, Dict, Any

AI_SERIES_DIR = Path(__file__).resolve().parent.parent / "AI_SERIES"
CURRICULUM_FILE = AI_SERIES_DIR / "AI_SERIES_CURRICULUM.md"
PROGRESS_FILE = AI_SERIES_DIR / "AI_SERIES_PROGRESS.md"
DAILY_POSTS_DIR = AI_SERIES_DIR / "DAILY_POSTS"

class AISeriesManager:
    """Manages the 90-day 'AI Explained: Zero to Advanced' curriculum, progress tracking, and daily lesson generation."""

    def __init__(self):
        DAILY_POSTS_DIR.mkdir(parents=True, exist_ok=True)

    def get_all_topics(self) -> list[Dict[str, Any]]:
        """Parses AI_SERIES_CURRICULUM.md to retrieve all 90 days with levels, chapters, and titles."""
        if not CURRICULUM_FILE.exists():
            return []

        with open(CURRICULUM_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        topics = []
        current_level = "Level 1: AI Fundamentals"
        current_chapter = "The Core Mental Model"

        for line in content.splitlines():
            line_str = line.strip()
            if "LEVEL 1:" in line_str:
                current_level = "Level 1: AI Fundamentals"
            elif "LEVEL 2:" in line_str:
                current_level = "Level 2: Modern AI & Generative Systems"
            elif "LEVEL 3:" in line_str:
                current_level = "Level 3: Advanced AI Engineering"
            elif line_str.startswith("### Chapter"):
                current_chapter = line_str.replace("###", "").strip()

            match = re.match(r"- \*\*Day (\d+):\*\* (.+)", line_str)
            if match:
                day_num = int(match.group(1))
                title = match.group(2).strip()
                topics.append({
                    "day": day_num,
                    "title": title,
                    "level": current_level,
                    "chapter": current_chapter
                })
        return topics

    def get_next_unpublished_day(self) -> Optional[Dict[str, Any]]:
        """Returns the next day topic that has not yet been published."""
        topics = self.get_all_topics()
        if not topics:
            return None

        # Check existing files in DAILY_POSTS
        existing_days = set()
        for post_file in DAILY_POSTS_DIR.glob("DAY_*.md"):
            m = re.search(r"DAY_(\d+)", post_file.name)
            if m:
                existing_days.add(int(m.group(1)))

        for t in topics:
            if t["day"] not in existing_days:
                return t

        # If all are generated, loop or return last
        return topics[0] if topics else None

    def record_published_day(self, day: int, topic_title: str, content: str, live_url: str = ""):
        """Saves DAY_XXX.md and updates the progress tracker."""
        file_path = DAILY_POSTS_DIR / f"DAY_{day:03d}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Day {day:03d}: {topic_title}\n\n{content}\n")

        # Update progress file
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                prog_content = f.read()

            target_row = f"| **{day:02d}** |"
            if target_row in prog_content:
                lines = prog_content.splitlines()
                updated_lines = []
                for line in lines:
                    if target_row in line:
                        parts = [p.strip() for p in line.split("|")]
                        # parts: ['', '**01**', 'Level 1', 'Title', 'Status', 'Date', 'Links', 'Notes', '']
                        if len(parts) >= 6:
                            parts[4] = "Published"
                            parts[5] = "Automated"
                            if live_url and len(parts) >= 7:
                                parts[6] = f"[LinkedIn]({live_url})"
                        updated_lines.append(" | ".join(parts))
                    else:
                        updated_lines.append(line)
                with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                    f.write("\n".join(updated_lines) + "\n")
