import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

class ActivityTracker:
    """
    Durable metrics & activity tracker designed for ephemeral CI runners
    and local execution. Records verifiable attempts, successes, failures, and skips.
    """

    def __init__(self, metrics_file: Path, history_file: Path):
        self.metrics_file = metrics_file
        self.history_file = history_file
        self.metrics = self._load_metrics()
        self.history = self._load_history()

    def _load_metrics(self) -> Dict[str, Any]:
        default_metrics = {
            "trial_meta": {
                "version": "1.0.0",
                "last_updated": None,
                "trial_start_utc": datetime.now(timezone.utc).isoformat(),
            },
            "lifetime_summary": {
                "total_cycles_executed": 0,
                "original_posts_attempted": 0,
                "original_posts_succeeded": 0,
                "replies_attempted": 0,
                "replies_succeeded": 0,
                "reposts_attempted": 0,
                "reposts_succeeded": 0,
                "actions_skipped": 0,
                "failed_operations": 0,
                "ai_generation_requests": 0,
                "ai_generation_failures": 0,
                "rate_limits_encountered": 0
            },
            "recent_events": []  # Keeps last 100 structured event records
        }
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Merge defaults for schema safety
                    for k, v in default_metrics["lifetime_summary"].items():
                        data.setdefault("lifetime_summary", {}).setdefault(k, v)
                    return data
            except Exception:
                pass
        return default_metrics

    def _load_history(self) -> Dict[str, List[str]]:
        default_history = {
            "posted_tweets": [],
            "replied_urls": [],
            "reposted_urls": []
        }
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data.setdefault("posted_tweets", [])
                    data.setdefault("replied_urls", [])
                    data.setdefault("reposted_urls", [])
                    return data
            except Exception:
                pass
        return default_history

    def save(self):
        """Persists metrics and post history atomically."""
        self.metrics["trial_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        try:
            with open(self.metrics_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, indent=2)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"[ActivityTracker] Error saving metrics/history: {e}")

    def get_today_counts(self) -> Dict[str, int]:
        """Calculates successful actions completed in the current UTC day."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        counts = {
            "original_posts": 0,
            "replies": 0,
            "reposts": 0,
            "total_actions": 0
        }
        for event in self.metrics.get("recent_events", []):
            if event.get("timestamp", "").startswith(today_str) and event.get("status") == "success":
                atype = event.get("action_type")
                if atype == "original_post":
                    counts["original_posts"] += 1
                    counts["total_actions"] += 1
                elif atype == "reply":
                    counts["replies"] += 1
                    counts["total_actions"] += 1
                elif atype in ("repost", "quote_tweet"):
                    counts["reposts"] += 1
                    counts["total_actions"] += 1
        return counts

    def record_event(
        self,
        action_type: str,
        status: str,  # 'success', 'failed', 'skipped', 'dry_run'
        target_identifier: str = "",
        content_preview: str = "",
        skip_or_error_reason: str = "",
        duration_seconds: float = 0.0,
        is_dry_run: bool = False
    ):
        """Records a granular event and increments corresponding aggregate counters."""
        now_utc = datetime.now(timezone.utc).isoformat()
        summary = self.metrics["lifetime_summary"]
        summary["total_cycles_executed"] += 1

        # Increment specific attempt and success counters
        if action_type == "original_post":
            summary["original_posts_attempted"] += 1
            if status == "success":
                summary["original_posts_succeeded"] += 1
                if target_identifier and target_identifier not in self.history["posted_tweets"]:
                    self.history["posted_tweets"].append(target_identifier)
        elif action_type == "reply":
            summary["replies_attempted"] += 1
            if status == "success":
                summary["replies_succeeded"] += 1
                if target_identifier and target_identifier not in self.history["replied_urls"]:
                    self.history["replied_urls"].append(target_identifier)
        elif action_type in ("repost", "quote_tweet"):
            summary["reposts_attempted"] += 1
            if status == "success":
                summary["reposts_succeeded"] += 1
                if target_identifier and target_identifier not in self.history["reposted_urls"]:
                    self.history["reposted_urls"].append(target_identifier)

        if status == "skipped":
            summary["actions_skipped"] += 1
        elif status == "failed":
            summary["failed_operations"] += 1
            if "rate limit" in skip_or_error_reason.lower() or "429" in skip_or_error_reason:
                summary["rate_limits_encountered"] += 1

        event_record = {
            "timestamp": now_utc,
            "action_type": action_type,
            "status": status,
            "is_dry_run": is_dry_run,
            "target": target_identifier,
            "content_preview": content_preview[:120] if content_preview else "",
            "reason": skip_or_error_reason,
            "duration_s": round(duration_seconds, 2)
        }

        # Keep rolling 150 events
        events = self.metrics.get("recent_events", [])
        events.append(event_record)
        if len(events) > 150:
            events = events[-150:]
        self.metrics["recent_events"] = events

        self.save()
