"""Durable idempotency state for non-X publishing actions.

The repository already persists ``post_history.json`` between local runs and
GitHub Actions.  This module stores platform-specific reservations in that
same file, so a timeout or a fresh CI runner cannot blindly submit the same
content again.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any, Dict, Optional, Tuple

from src.x_state import atomic_write_json, load_x_history, utc_now_iso, x_history_lock


def stable_hash(value: str) -> str:
    normalized = " ".join(str(value or "").split()).casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _platform_bucket(history: Dict[str, Any], platform: str) -> Dict[str, Any]:
    all_platforms = history.setdefault("platform_history", {})
    bucket = all_platforms.setdefault(
        platform,
        {"completed": [], "pending": []},
    )
    bucket.setdefault("completed", [])
    bucket.setdefault("pending", [])
    return bucket


def reserve_platform_action(
    history_file,
    *,
    platform: str,
    action_type: str,
    identity: str,
    target: str = "",
    preview: str = "",
) -> Tuple[Optional[str], str]:
    """Atomically reserve a platform action before submitting it."""

    if not identity:
        raise ValueError("Platform action identity cannot be empty")

    with x_history_lock(history_file):
        history = load_x_history(history_file)
        bucket = _platform_bucket(history, platform)
        if identity in bucket["completed"]:
            return None, f"{platform} action is already completed."
        for entry in bucket["pending"]:
            if isinstance(entry, dict) and entry.get("identity") == identity:
                if entry.get("status") in {"reserved", "unknown"}:
                    return None, f"{platform} action is already reserved."

        reservation_id = uuid.uuid4().hex
        bucket["pending"].append(
            {
                "reservation_id": reservation_id,
                "identity": identity,
                "action_type": action_type,
                "target": target,
                "preview": preview[:160],
                "status": "reserved",
                "reserved_at": utc_now_iso(),
            }
        )
        atomic_write_json(history_file, history)
        return reservation_id, "Reserved"


def complete_platform_action(
    history_file,
    reservation_id: str,
    *,
    outcome: str,
    reason: str = "",
) -> None:
    """Complete an action; retain unknown outcomes to block unsafe retries."""

    if outcome not in {"success", "failed", "unknown"}:
        raise ValueError(f"Unsupported platform action outcome: {outcome}")

    with x_history_lock(history_file):
        history = load_x_history(history_file)
        platforms = history.setdefault("platform_history", {})
        matched = None
        for platform, bucket in platforms.items():
            if not isinstance(bucket, dict):
                continue
            pending = bucket.setdefault("pending", [])
            remaining = []
            for entry in pending:
                if isinstance(entry, dict) and entry.get("reservation_id") == reservation_id and matched is None:
                    matched = (platform, bucket, entry)
                else:
                    remaining.append(entry)
            bucket["pending"] = remaining

        if matched is None:
            return

        _platform, bucket, entry = matched
        if outcome == "success":
            identity = entry.get("identity")
            if identity and identity not in bucket["completed"]:
                bucket["completed"].append(identity)
        elif outcome == "unknown":
            entry["status"] = "unknown"
            entry["unknown_at"] = utc_now_iso()
            entry["reason"] = reason[:500]
            bucket["pending"].append(entry)

        for bucket in platforms.values():
            if isinstance(bucket, dict) and len(bucket.get("completed", [])) > 500:
                bucket["completed"] = bucket["completed"][-500:]
        atomic_write_json(history_file, history)


def platform_action_seen(history_file, *, platform: str, identity: str) -> bool:
    history = load_x_history(history_file)
    bucket = history.get("platform_history", {}).get(platform, {})
    if identity in bucket.get("completed", []):
        return True
    return any(
        isinstance(entry, dict)
        and entry.get("identity") == identity
        and entry.get("status") in {"reserved", "unknown"}
        for entry in bucket.get("pending", [])
    )
