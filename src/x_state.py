"""Durable, atomic state helpers for X publishing.

X publishing is browser-driven, so a request can be accepted even when the
browser or network times out before the caller sees a response.  These
helpers reserve an action before submission and keep an unknown result
reserved, preventing an automatic retry from creating a duplicate post.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple


LOCK_TIMEOUT_SECONDS = 30.0
STALE_LOCK_SECONDS = 180.0


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def prepare_x_text(text: str) -> str:
    """Apply the same length limit before hashing and publishing an X post."""

    value = str(text or "").strip()
    if len(value) <= 275:
        return value
    shortened = value[:270].rsplit(" ", 1)[0].rstrip(".,:;")
    return f"{shortened}..."


def normalize_x_text(text: str) -> str:
    """Normalize harmless whitespace/case differences for deduplication."""

    return " ".join(prepare_x_text(text).split()).casefold()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_x_text(text).encode("utf-8")).hexdigest()


def _default_history() -> Dict[str, Any]:
    return {
        "posted_tweets": [],
        "replied_urls": [],
        "reposted_urls": [],
        "posted_tweet_hashes": [],
        "pending_x_actions": [],
    }


def _ensure_schema(data: Any) -> Dict[str, Any]:
    result = data if isinstance(data, dict) else {}
    defaults = _default_history()
    for key, value in defaults.items():
        if key not in result or not isinstance(result[key], type(value)):
            result[key] = value.copy() if isinstance(value, list) else value
    return result


def load_x_history(history_file: Path) -> Dict[str, Any]:
    """Load X history while remaining compatible with the old list-only file."""

    try:
        with history_file.open("r", encoding="utf-8") as handle:
            return _ensure_schema(json.load(handle))
    except (OSError, ValueError, TypeError):
        return _default_history()


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """Write JSON atomically in the destination directory."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def _lock_path(history_file: Path) -> Path:
    # Keep lock files outside the repository so a killed process cannot leave
    # an untracked file in the user's working tree.
    digest = hashlib.sha256(str(history_file.resolve()).encode("utf-8")).hexdigest()[:20]
    return Path(tempfile.gettempdir()) / f"neubench-x-history-{digest}.lock"


@contextmanager
def x_history_lock(history_file: Path) -> Iterator[None]:
    """Cross-process lock for local X history reservations."""

    lock_file = _lock_path(history_file)
    deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
    acquired = False
    while time.monotonic() < deadline:
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(f"{os.getpid()}\n{utc_now_iso()}\n")
            acquired = True
            break
        except FileExistsError:
            try:
                if time.time() - lock_file.stat().st_mtime > STALE_LOCK_SECONDS:
                    lock_file.unlink(missing_ok=True)
                    continue
            except OSError:
                pass
            time.sleep(0.05)

    if not acquired:
        raise TimeoutError("Timed out waiting for the X history lock")

    try:
        yield
    finally:
        try:
            lock_file.unlink()
        except FileNotFoundError:
            pass


def _pending_match(
    history: Dict[str, Any],
    *,
    action_type: str,
    target_identifier: str = "",
    body_hash: str = "",
) -> bool:
    for entry in history.get("pending_x_actions", []):
        if not isinstance(entry, dict) or entry.get("action_type") != action_type:
            continue
        if entry.get("status") not in {"reserved", "unknown"}:
            continue
        if body_hash and entry.get("content_hash") == body_hash:
            return True
        if target_identifier and entry.get("target_identifier") == target_identifier:
            return True
    return False


def reserve_original(
    history_file: Path,
    *,
    target_identifier: str,
    text: str,
) -> Tuple[Optional[str], str]:
    """Reserve an original X post before browser submission."""

    body_hash = content_hash(text)
    with x_history_lock(history_file):
        history = load_x_history(history_file)
        if body_hash in history["posted_tweet_hashes"] or _pending_match(
            history,
            action_type="original_post",
            body_hash=body_hash,
        ):
            return None, "This X post body is already published or reserved."

        reservation_id = uuid.uuid4().hex
        history["pending_x_actions"].append(
            {
                "reservation_id": reservation_id,
                "action_type": "original_post",
                "target_identifier": target_identifier,
                "content_hash": body_hash,
                "content_preview": prepare_x_text(text)[:120],
                "status": "reserved",
                "reserved_at": utc_now_iso(),
            }
        )
        atomic_write_json(history_file, history)
        return reservation_id, "Reserved"


def reserve_target(
    history_file: Path,
    *,
    action_type: str,
    target_identifier: str,
    text: str = "",
) -> Tuple[Optional[str], str]:
    """Reserve a reply or quote target before browser submission."""

    if action_type not in {"reply", "repost"}:
        raise ValueError(f"Unsupported X target action: {action_type}")

    history_key = "replied_urls" if action_type == "reply" else "reposted_urls"
    body_hash = content_hash(text) if text else ""
    with x_history_lock(history_file):
        history = load_x_history(history_file)
        if target_identifier in history[history_key] or _pending_match(
            history,
            action_type=action_type,
            target_identifier=target_identifier,
        ):
            return None, f"This X {action_type} target is already completed or reserved."

        reservation_id = uuid.uuid4().hex
        history["pending_x_actions"].append(
            {
                "reservation_id": reservation_id,
                "action_type": action_type,
                "target_identifier": target_identifier,
                "content_hash": body_hash,
                "content_preview": prepare_x_text(text)[:120] if text else "",
                "status": "reserved",
                "reserved_at": utc_now_iso(),
            }
        )
        atomic_write_json(history_file, history)
        return reservation_id, "Reserved"


def complete_reservation(
    history_file: Path,
    reservation_id: str,
    *,
    outcome: str,
    target_identifier: str = "",
    text: str = "",
    reason: str = "",
) -> None:
    """Finalize a reservation; keep unknown outcomes blocked from retries."""

    if outcome not in {"success", "failed", "unknown"}:
        raise ValueError(f"Unsupported X reservation outcome: {outcome}")

    with x_history_lock(history_file):
        history = load_x_history(history_file)
        pending = history["pending_x_actions"]
        matched = None
        remaining = []
        for entry in pending:
            if isinstance(entry, dict) and entry.get("reservation_id") == reservation_id and matched is None:
                matched = entry
            else:
                remaining.append(entry)

        if matched is None:
            return

        final_target = target_identifier or matched.get("target_identifier", "")
        action_type = matched.get("action_type", "original_post")
        if outcome == "success":
            if action_type == "original_post":
                if final_target and final_target not in history["posted_tweets"]:
                    history["posted_tweets"].append(final_target)
                body_hash = matched.get("content_hash") or (content_hash(text) if text else "")
                if body_hash and body_hash not in history["posted_tweet_hashes"]:
                    history["posted_tweet_hashes"].append(body_hash)
            elif action_type == "reply":
                if final_target and final_target not in history["replied_urls"]:
                    history["replied_urls"].append(final_target)
            elif action_type == "repost":
                if final_target and final_target not in history["reposted_urls"]:
                    history["reposted_urls"].append(final_target)
        elif outcome == "unknown":
            matched["status"] = "unknown"
            matched["unknown_at"] = utc_now_iso()
            matched["reason"] = reason[:500]
            remaining.append(matched)

        history["pending_x_actions"] = remaining
        atomic_write_json(history_file, history)


def is_original_topic_seen(history_file: Path, target_identifier: str) -> bool:
    history = load_x_history(history_file)
    return target_identifier in history.get("posted_tweets", [])


def trim_history(history_file: Path, limit: int = 500) -> None:
    """Bound durable X lists without removing active unknown reservations."""

    with x_history_lock(history_file):
        history = load_x_history(history_file)
        for key in ("posted_tweets", "posted_tweet_hashes", "replied_urls", "reposted_urls"):
            if len(history.get(key, [])) > limit:
                history[key] = history[key][-limit:]
        atomic_write_json(history_file, history)
