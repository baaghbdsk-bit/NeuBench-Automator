"""Growth-focused publishing helpers.

The accounts are run as creator accounts, not as a product brand. This module
keeps published text clean (no brand names, no outbound links that suppress
reach) and blocks near-duplicate topics from being recycled.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence, Tuple

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
        # Brand removal can leave a lowercase clause after a full stop.
        line = re.sub(
            r"(?<=[.!?])\s+([a-z])",
            lambda m: " " + m.group(1).upper(),
            line,
        )
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


# ==============================================================================
# EVIDENCE GATE — quality is correctness, not taste
# ==============================================================================

_NUMERIC_CLAIM_RE = re.compile(
    r"\b\d[\d,]*\+?(?:\.\d+)?\+?\s*[KMB]?\+?\s*(?:"
    r"%|percent\b|percentage\b|×|x\b|times?\b|"
    r"ms\b|milliseconds?\b|µs\b|us\b|microseconds?\b|ns\b|nanoseconds?\b|"
    r"seconds?\b|minutes?\b|hours?\b|days?\b|"
    r"[KMGT]?B(?:/s)?\b|GB/s\b|TB/s\b|IOPS\b|qps\b|reqs?/s\b|"
    r"tokens?\b|cycles?\b|bits?\b|bytes?\b|writes?\b|reads?\b|"
    r"models?\b|logs?\b|papers?\b|"
    r"thousand\b|million\b|billion\b|trillion\b|"
    r"per\s+second\b)",
    re.IGNORECASE,
)

_BANNED_OPENERS_RE = re.compile(
    r"^\s*(?:what\s+is\b|understanding\s+the\s+real[- ]world\s+mechanics\b|"
    r"in\s+today'?s\b|let'?s\s+dive\s+in\b|game\s+changer\b|unlock\b|"
    r"the\s+future\s+of\b|your\s+.{0,80}?\s+(?:yet|but)\b|every\s+\w+\s+(?:time|context switch)\b|"
    r"imagine\b)",
    re.IGNORECASE,
)

_BROKEN_TEMPLATE_RE = re.compile(
    r"understanding\s+the\s+real[- ]world\s+mechanics\s+of\b|"
    r"is\s+one\s+of\s+the\s+most\s+critical\s+fundamentals\b|"
    r"what\s+is\s+.{0,80}\?\s+is\b",
    re.IGNORECASE,
)

_ABSOLUTE_CLAIM_RE = re.compile(
    r"\b(?:guaranteed|100\s*%|eliminat(?:e|es|ed|ing)|provably|"
    r"impossible\s+to\s+fail|never\s+fails?|always\s+works?)\b",
    re.IGNORECASE,
)

# A confident personal story the model invented ("I spent a week debugging...")
# is the same class of defect as a fake benchmark number.
_INVENTED_ANecdOTE_RE = re.compile(
    r"\bI\s+(?:spent|wasted|burnt|burned)\s+(?:a|an|\d+)\s*"
    r"(?:week|weeks|month|months|day|days|hour|hours|year|years)\b|"
    r"\bour\s+(?:team|cluster|service|production)\b.{0,80}\b(?:we|I)\s+(?:saw|found|debugged|measured)\b",
    re.IGNORECASE,
)
_VOICE_CONNECTOR_RE = re.compile(
    r"\b(?:because|when|after|until|the reason|it turns out|here is|"
    r"the cost|the cause|the part that|what breaks|the mistake)\b",
    re.IGNORECASE,
)

_STRUCTURAL_NUMBER_RE = re.compile(
    r"^(?:Day\s+\d+\s*/\s*\d+|Step\s+\d+|\d+[.)]\s|[A-Z][A-Za-z0-9]*-\d+)$"
)


def _normalize_claim(raw: str) -> str:
    """Canonical value+unit so '60 percent' and '60%' compare equal."""
    value = raw.strip().rstrip(".,;:").replace(",", "").lower()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s*(?:k|m|b)(?=\s|$)", lambda m: m.group(0).strip(), value)
    # µ is not a word character, so \bµs\b never matches. Handle it directly.
    value = value.replace("µs", "us").replace("μs", "us")
    for surface, canonical in (
        ("percent", "%"), ("percentage", "%"),
        ("milliseconds", "ms"), ("millisecond", "ms"),
        ("microseconds", "us"),
        ("nanoseconds", "ns"), ("nanosecond", "ns"),
        ("seconds", "s"), ("second", "s"),
        ("minutes", "min"), ("minute", "min"),
        ("hours", "h"), ("hour", "h"),
    ):
        value = re.sub(rf"\b{surface}\b", canonical, value)
    # "5 microseconds" and "5µs" must compare equal.
    value = re.sub(r"\s+(?=%|ms\b|us\b|ns\b|s\b|min\b|h\b)", "", value)
    return value.strip()


def extract_numeric_claims(text: str) -> List[str]:
    """Return every quantitative claim in a draft."""
    return [match.group(0) for match in _NUMERIC_CLAIM_RE.finditer(text or "")]


def validate_no_number_without_source(
    text: str, source_context: str = ""
) -> Tuple[bool, List[str]]:
    """No number ships unless the same value+unit exists in the source context."""
    sourced = {_normalize_claim(c) for c in extract_numeric_claims(source_context or "")}
    issues = []
    for claim in extract_numeric_claims(text):
        if _STRUCTURAL_NUMBER_RE.match(claim.strip()):
            continue
        if _normalize_claim(claim) not in sourced:
            issues.append(f"unsourced number: {claim.strip()}")
    return not issues, issues


def validate_no_banned_openers(text: str) -> Tuple[bool, List[str]]:
    first_line = str(text or "").split("\n", 1)[0].strip()
    if not first_line:
        return False, ["first line is empty"]
    if _BANNED_OPENERS_RE.search(first_line):
        return False, [f"banned opener: {first_line[:80]}"]
    if first_line.endswith("?"):
        return False, ["first line is a question, not a claim"]
    return True, []


def validate_no_broken_template(text: str) -> Tuple[bool, List[str]]:
    match = _BROKEN_TEMPLATE_RE.search(text or "")
    if match:
        return False, [f"broken template: {match.group(0)[:80]}"]
    return True, []


def validate_no_repeated_title(text: str, topic_title: str = "") -> Tuple[bool, List[str]]:
    title = str(topic_title or "").strip()
    if len(title) < 8:
        return True, []
    head = str(text or "")[:400].lower()
    needle = title.lower().rstrip("?")
    if head.count(needle) > 1:
        return False, ["topic title repeated in the opening"]
    return True, []


def validate_no_absolute_claims(text: str) -> Tuple[bool, List[str]]:
    issues = [m.group(0) for m in _ABSOLUTE_CLAIM_RE.finditer(text or "")]
    return not issues, [f"absolute claim: {i}" for i in issues]


def validate_one_question(text: str) -> Tuple[bool, List[str]]:
    """Exactly one genuine closing question, never generic bait."""
    body = str(text or "")
    questions = body.count("?")
    if questions == 0:
        return False, ["no closing question"]
    if questions > 2:
        return False, [f"too many questions ({questions})"]
    tail = body.rstrip().split("\n")[-1].strip()
    if _BANNED_OPENERS_RE.search(tail) or re.search(
        r"thoughts\s*\?|what\s+do\s+you\s+think|agree\s*\?|let\s+me\s+know|comment\s+below",
        tail, re.IGNORECASE,
    ):
        return False, ["bait question"]
    if len(tail) > 120:
        return False, ["closing question too long"]
    return True, []


_VOICE_FIRST_PERSON_RE = re.compile(
    r"\b(I|I've|I'd|I'm|I've|my|mine|we|we've|our|ours)\b", re.IGNORECASE
)
_VOICE_STAKES = (
    "cost", "latency", "memory", "broke", "failed", "wrong", "trade",
    "stall", "bottleneck", "gap", "leak", "slow", "expensive", "risk",
    "silent", "debug", "production", "regret", "wrong", "failure",
)
_VOICE_STANCE = (
    "wrong default", "overrated", "underrated", "I would not", "I'd take",
    "I stopped", "I switched", "stop calling", "beats", "loses to",
    "most teams", "the default is", "not worth", "hard disagree",
    "I changed my mind", "I used to", "I'd rather",
)
_VOICE_TECHNICAL = (
    "kv cache", "io_uring", "wal", "softmax", "bloom filter", "p99", "ttft",
    "context window", "quantization", "inference", "token", "latency",
    "memory", "index", "scheduler", "kernel", "embedding", "rag",
    "fine-tuning", "routing", "cache", "throughput", "gpu", "batch",
)


def voice_quality_score(text: str, topic_title: str = "") -> Tuple[int, dict]:
    """0–10 rubric: point of view, stakes, arguable stance, specificity, clean open."""
    body = str(text or "")
    lines = [line for line in body.split("\n") if line.strip()]
    head = " ".join(lines[:2])
    head3 = " ".join(lines[:3]).lower()
    low = body.lower()

    if re.match(r"^\s*(I\b|I've\b|I'd\b|I'm\b)", head, re.IGNORECASE):
        pov = 2
    elif _VOICE_FIRST_PERSON_RE.search(head):
        pov = 1
    else:
        pov = 0

    stakes_hits = sum(1 for word in _VOICE_STAKES if word in head.lower())
    stakes = 2 if stakes_hits >= 2 else 1 if stakes_hits else 0

    stance = 2 if any(marker.lower() in head3 for marker in _VOICE_STANCE) else (
        1 if any(marker.lower() in low for marker in _VOICE_STANCE) else 0
    )

    topic_tokens = _topic_tokens(topic_title)
    tech_hits = sum(1 for noun in _VOICE_TECHNICAL if noun in low)
    topic_hits = sum(1 for token in topic_tokens if token in low)
    detail = tech_hits + min(topic_hits, 2)
    specificity = 2 if detail >= 2 else 1 if detail else 0

    clean = 0 if _BANNED_OPENERS_RE.search(head) or head.endswith("?") else 2

    # A keyword-stuffed first line with no causal explanation is still a
    # generic post. Require an actual mechanism explanation in the first lines.
    if not _VOICE_CONNECTOR_RE.search(head3):
        stance = min(stance, 1)
        stakes = min(stakes, 1)

    score = pov + stakes + stance + specificity + clean
    return score, {
        "pov": pov, "stakes": stakes, "stance": stance,
        "specificity": specificity, "clean_open": clean,
    }


def evidence_gate(
    text: str,
    *,
    topic_title: str = "",
    source_context: str = "",
    require_question: bool = True,
    require_voice: bool = False,
) -> Tuple[bool, str, List[str]]:
    """Master pre-publish gate. Returns (ok, text, violations).

    Never silently edits numbers: a stripped digit creates a different false
    claim. Callers must regenerate once and then skip the post.
    """
    cleaned = sanitize_publish_text(text)
    issues: List[str] = []
    checks = [
        validate_no_broken_template(cleaned),
        validate_no_repeated_title(cleaned, topic_title),
        validate_no_number_without_source(cleaned, source_context),
        validate_no_absolute_claims(cleaned),
        validate_no_banned_openers(cleaned),
    ]
    if _INVENTED_ANecdOTE_RE.search(cleaned) and not source_context:
        issues.append("invented personal anecdote with no source")
    if require_question:
        checks.append(validate_one_question(cleaned))
    for ok, problems in checks:
        if not ok:
            issues.extend(problems)
    if require_voice:
        score, parts = voice_quality_score(cleaned, topic_title)
        if score < 7 or parts["pov"] < 1 or parts["specificity"] < 1:
            issues.append(f"weak voice {score}/10: {parts}")
    return not issues, cleaned, issues


def first_comment_gate(text: str) -> Tuple[bool, str, List[str]]:
    """First comment adds value, not a second question or a link."""
    cleaned = sanitize_publish_text(text)
    issues: List[str] = []
    if not cleaned:
        return False, cleaned, ["first comment is empty"]
    if len(cleaned) > 350:
        issues.append("first comment too long")
    if "?" in cleaned:
        issues.append("first comment asks a second question")
    if re.search(r"https?://|www\.", cleaned, re.IGNORECASE):
        issues.append("first comment contains a link")
    ok, num_issues = validate_no_number_without_source(cleaned, "")
    issues.extend(num_issues)
    return not issues, cleaned, issues
