"""Durable LinkedIn publishing and engagement state helpers.

The LinkedIn workflows run on fresh CI machines, so the state used for
deduplication and cadence must be explicit, backward-compatible, and written
atomically.  This module keeps that policy separate from the browser/API
implementation.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

import config


POST_HISTORY_FILE = config.BASE_DIR / "linkedin_post_history.json"
ENGAGEMENT_HISTORY_FILE = config.BASE_DIR / "linkedin_engagement_history.json"
POST_HISTORY_VERSION = 2
MAX_HISTORY_ENTRIES = 500


def utc_now_iso() -> str:
    """Return a timezone-aware UTC timestamp suitable for JSON state."""

    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(value: Any) -> Optional[datetime]:
    """Parse an ISO timestamp, returning ``None`` for malformed values."""

    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def cadence_slot_key(value: Any) -> str:
    """Return the three-hour UTC slot used by the scheduled LinkedIn workflow."""

    parsed = value if isinstance(value, datetime) else parse_timestamp(value)
    if parsed is None:
        return ""
    parsed = parsed.astimezone(timezone.utc)
    anchor = parsed.replace(hour=0, minute=15, second=0, microsecond=0)
    if parsed < anchor:
        anchor -= timedelta(days=1)
    slot_number = int((parsed - anchor).total_seconds() // (3 * 60 * 60))
    return (anchor + timedelta(hours=slot_number)).isoformat()


def normalize_text(value: Any) -> str:
    """Normalize text for stable, case-insensitive comparisons."""

    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\ufffd", "'")).strip().casefold()


def canonical_url(value: Any) -> str:
    """Remove tracking/query fragments from a source URL."""

    url = str(value or "").strip()
    if not url:
        return ""
    return url.split("#", 1)[0].split("?", 1)[0].rstrip("/").casefold()


def content_hash(value: Any) -> str:
    """Create a stable digest for exact/near-exact generated content checks."""

    normalized = normalize_text(value)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


def topic_key(title: Any, url: Any = "") -> str:
    """Create a stable key from a canonical source URL or normalized title."""

    source_url = canonical_url(url)
    # NeuBench topics intentionally share the product homepage URL; their
    # titles are the meaningful identity in that case.
    if source_url and "app.neubench.workers.dev" not in source_url:
        return f"url:{source_url}"
    return f"title:{content_hash(title)}"


def engagement_key(kind: str, target: Any, author: Any = "", body: Any = "") -> str:
    """Create a stable key for a comment or reply target."""

    material = "|".join(
        (normalize_text(part) for part in (kind, target, author, body))
    )
    return f"{normalize_text(kind)}:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:32]}"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, TypeError, ValueError):
        return default


def save_json_atomic(path: Path, payload: Any) -> None:
    """Write JSON using replace semantics so interrupted writes do not corrupt state."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def _clean_post_entry(entry: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(entry, dict):
        return None
    title = str(entry.get("title", "")).strip()
    url = str(entry.get("url", "")).strip()
    if not title and not url:
        return None
    return {
        "topic_key": str(entry.get("topic_key") or topic_key(title, url)),
        "title": title,
        "url": url,
        "content_hash": str(entry.get("content_hash", "")),
        "status": str(entry.get("status", "success")),
        "posted_at": str(entry.get("posted_at", "")),
        "post_urn": str(entry.get("post_urn", "")),
        "visual_format": str(entry.get("visual_format", "")),
    }


def load_post_history(path: Path = POST_HISTORY_FILE) -> Dict[str, Any]:
    """Load current or legacy LinkedIn post history into the v2 shape."""

    raw = _read_json(path, {})
    if isinstance(raw, list):
        raw = {"posted_titles": raw}
    if not isinstance(raw, dict):
        raw = {}

    entries: List[Dict[str, Any]] = []
    for item in raw.get("posts", []):
        cleaned = _clean_post_entry(item)
        if cleaned:
            entries.append(cleaned)

    # Migrate the old exact-title-only format without losing its dedupe data.
    existing_titles = {normalize_text(item.get("title")) for item in entries}
    for legacy in raw.get("posted_titles", []):
        title = str(legacy or "")
        if title.startswith("li:"):
            title = title[3:]
        if not title or normalize_text(title) in existing_titles:
            continue
        entries.append(
            {
                "topic_key": topic_key(title),
                "title": title,
                "url": "",
                "content_hash": "",
                "status": "success",
                "posted_at": "",
                "post_urn": "",
            }
        )
        existing_titles.add(normalize_text(title))

    return {
        "version": POST_HISTORY_VERSION,
        "last_success_at": raw.get("last_success_at"),
        "last_unknown_at": raw.get("last_unknown_at"),
        "posts": entries[-MAX_HISTORY_ENTRIES:],
    }


def save_post_history(state: Dict[str, Any], path: Path = POST_HISTORY_FILE) -> None:
    """Persist post history while retaining the legacy summary field."""

    entries = [item for item in state.get("posts", []) if isinstance(item, dict)][-MAX_HISTORY_ENTRIES:]
    payload = {
        "version": POST_HISTORY_VERSION,
        "last_success_at": state.get("last_success_at"),
        "last_unknown_at": state.get("last_unknown_at"),
        "posts": entries,
        "posted_titles": [f"li:{item.get('title', '')}" for item in entries if item.get("title")],
    }
    save_json_atomic(path, payload)


def append_post_entry(
    state: Dict[str, Any],
    *,
    title: str,
    url: str = "",
    content: str = "",
    status: str = "success",
    posted_at: Optional[str] = None,
    post_urn: str = "",
    visual_format: str = "",
) -> Dict[str, Any]:
    """Append a successful or outcome-unknown attempt to post history."""

    timestamp = posted_at or utc_now_iso()
    entry = {
        "topic_key": topic_key(title, url),
        "title": str(title).strip(),
        "url": str(url or "").strip(),
        "content_hash": content_hash(content),
        "status": status,
        "posted_at": timestamp,
        "post_urn": post_urn,
        "visual_format": str(visual_format or "").strip(),
    }
    state.setdefault("posts", []).append(entry)
    state["posts"] = state["posts"][-MAX_HISTORY_ENTRIES:]
    if status == "success":
        state["last_success_at"] = timestamp
    elif status in {"unknown", "pending"}:
        state["last_unknown_at"] = timestamp
    return entry


def post_is_duplicate(
    state: Dict[str, Any],
    *,
    title: str,
    url: str = "",
    content: str = "",
) -> bool:
    """Return whether a topic, source URL, or generated body was already used."""

    normalized_title = normalize_text(title)
    source_url = canonical_url(url)
    generated_hash = content_hash(content)
    key = topic_key(title, url)
    for entry in state.get("posts", []):
        if not isinstance(entry, dict):
            continue
        if entry.get("topic_key") == key:
            return True
        if normalized_title and normalize_text(entry.get("title")) == normalized_title:
            return True
        if source_url and "app.neubench.workers.dev" not in source_url and canonical_url(entry.get("url")) == source_url:
            return True
        if generated_hash and entry.get("content_hash") == generated_hash:
            return True
    return False


def _state_post_times(state: Dict[str, Any]) -> Iterable[datetime]:
    for field in ("last_success_at", "last_unknown_at"):
        parsed = parse_timestamp(state.get(field))
        if parsed:
            yield parsed
    for entry in state.get("posts", []):
        if isinstance(entry, dict) and entry.get("status") in {"success", "unknown", "pending"}:
            parsed = parse_timestamp(entry.get("posted_at"))
            if parsed:
                yield parsed


def last_post_at(
    state: Dict[str, Any],
    events: Optional[Iterable[Dict[str, Any]]] = None,
) -> Optional[datetime]:
    """Return the latest durable or metrics-backed LinkedIn post attempt."""

    candidates = list(_state_post_times(state))
    for event in events or []:
        if not isinstance(event, dict):
            continue
        if event.get("action_type") != "linkedin_post":
            continue
        if event.get("is_dry_run") or event.get("status") != "success":
            continue
        parsed = parse_timestamp(event.get("timestamp"))
        if parsed:
            candidates.append(parsed)
    return max(candidates) if candidates else None


def count_posts_on_date(state: Dict[str, Any], date_prefix: str) -> int:
    """Count successful or unknown post attempts for a UTC date."""

    return sum(
        1
        for entry in state.get("posts", [])
        if isinstance(entry, dict)
        and entry.get("status") in {"success", "unknown", "pending"}
        and str(entry.get("posted_at", "")).startswith(date_prefix)
    )


def load_engagement_history(path: Path = ENGAGEMENT_HISTORY_FILE) -> List[Dict[str, Any]]:
    """Load engagement history from the current or legacy list format."""

    raw = _read_json(path, {})
    if isinstance(raw, dict):
        raw = raw.get("engagements", [])
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict) and item.get("key")][-1000:]


def save_engagement_history(
    entries: Iterable[Dict[str, Any]],
    path: Path = ENGAGEMENT_HISTORY_FILE,
) -> None:
    """Persist engagement keys atomically."""

    save_json_atomic(path, {"version": 2, "engagements": list(entries)[-1000:]})


def engagement_count_on_date(entries: Iterable[Dict[str, Any]], date_prefix: str) -> int:
    return sum(
        1
        for entry in entries
        if isinstance(entry, dict) and str(entry.get("ts", "")).startswith(date_prefix)
    )


@contextmanager
def linkedin_state_lock() -> Iterator[None]:
    """Serialize local LinkedIn publish/engagement state transitions."""

    lock_path = Path(tempfile.gettempdir()) / "neubench-linkedin-state.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        if os.name == "nt":
            import msvcrt

            lock_handle.seek(0)
            lock_handle.write("0")
            lock_handle.flush()
            lock_handle.seek(0)
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_handle.seek(0)
                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
