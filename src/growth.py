"""Growth-focused publishing helpers.

The accounts are run as creator accounts, not as a product brand. This module
keeps published text clean (no brand names, no outbound links that suppress
reach) and blocks near-duplicate topics from being recycled.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Sequence

_BRAND_RE = re.compile(r"\bneu\s*[-_]?\s*bench\b", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[^\s)>\]]+", re.IGNORECASE)
_BARE_BRAND_URL_RE = re.compile(
    r"\b(?:app\.)?neubench\.(?:workers\.dev|vercel\.app)\b\S*",
    re.IGNORECASE,
)
_CONNECTOR_RE = re.compile(
    r"\b(?:live\s+)?(?:on|at|via|from|using)\s*(?=[.,;:!?]|$)",
    re.IGNORECASE,
)
# Only strip these labels when they are all that is left after a URL is
# removed, never when a legitimate heading like "BENCHMARK: what to measure"
# starts a line.
_DEAD_LABEL_RE = re.compile(
    r"[ \t]*(?:\b(?:live\s+(?:evals|benchmarks?)|benchmarks?|compare\s+live|"
    r"full\s+eval\s+breakdown|tracking\s+real[- ]time)\s*[:|][ \t]*)+$",
    re.IGNORECASE | re.MULTILINE,
)

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "into", "is", "it", "its", "of", "on", "or", "that", "the", "their",
    "this", "to", "vs", "versus", "what", "when", "where", "which", "who",
    "why", "with", "your", "you", "we", "our", "not", "no", "do", "does",
}


def sanitize_publish_text(text: str) -> str:
    """Remove brand names and outbound links from text that is about to publish."""
    if not text:
        return text or ""

    out = str(text)
    out = _URL_RE.sub("", out)
    out = _BARE_BRAND_URL_RE.sub("", out)
    out = _BRAND_RE.sub("", out)
    out = _DEAD_LABEL_RE.sub("", out)
    out = _CONNECTOR_RE.sub("", out)
    out = re.sub(r"\(\s*\)", "", out)
    out = re.sub(r"\[\s*\]", "", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"[:|]\s*[-–—]\s+", ": ", out)
    out = re.sub(r"\s+([,.;:!?])", r"\1", out)
    out = re.sub(r"([,;:])\1+", r"\1", out)
    out = re.sub(r"[ \t]+\n", "\n", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    out = re.sub(r"^\s*[-–—|•·]\s*", "", out, flags=re.MULTILINE)
    out = out.strip(" \t-–—|:•·")
    return _fix_line_starts(out)


def _fix_line_starts(text: str) -> str:
    """Repair lines left lowercase or empty after removing a brand mention."""
    lines = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if line[0].isalpha() and line[0].islower():
            line = line[0].upper() + line[1:]
        lines.append(line)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def sanitize_plan(plan: dict) -> dict:
    """Recursively sanitize every string inside a generated content plan."""
    if not isinstance(plan, dict):
        return plan
    cleaned: dict = {}
    for key, value in plan.items():
        if isinstance(value, str):
            cleaned[key] = sanitize_publish_text(value)
        elif isinstance(value, dict):
            cleaned[key] = sanitize_plan(value)
        elif isinstance(value, list):
            cleaned[key] = [
                sanitize_plan(item) if isinstance(item, dict)
                else sanitize_publish_text(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            cleaned[key] = value
    return cleaned


def _topic_tokens(text: str) -> set:
    return {
        word
        for word in re.findall(r"[a-z0-9]+", str(text or "").lower())
        if len(word) > 2 and word not in _STOPWORDS
    }


def topic_similarity(left: str, right: str) -> float:
    """Jaccard similarity between two topic titles."""
    a, b = _topic_tokens(left), _topic_tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def is_near_duplicate_topic(
    title: str,
    recent_titles: Iterable[str],
    threshold: float = 0.55,
) -> bool:
    """Return True when a topic is too close to anything recently published."""
    if not title:
        return False
    return any(
        topic_similarity(title, previous) >= threshold
        for previous in recent_titles
        if previous
    )


def filter_fresh_topics(
    topics: Sequence[dict],
    recent_titles: Iterable[str],
    *,
    limit: int,
    threshold: float = 0.55,
) -> List[dict]:
    """Keep topics that do not repeat anything in the recent window."""
    recent = [str(t) for t in recent_titles if t]
    fresh: List[dict] = []
    chosen: List[str] = []
    for topic in topics:
        title = str(topic.get("title", ""))
        if not title:
            continue
        if is_near_duplicate_topic(title, recent + chosen, threshold):
            continue
        fresh.append(topic)
        chosen.append(title)
        if len(fresh) >= limit:
            break
    return fresh
