import os
from datetime import datetime, timezone
from typing import Tuple, Dict

class SafetyEngine:
    """
    Enforces rate limits, daily caps, trial time boundaries,
    and dry-run guards to ensure safe, compliant operation.
    """

    def __init__(self):
        # Global enable/disable switch
        self.trial_enabled = os.getenv("TRIAL_ENABLED", "true").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

        # Per-action enable switches
        self.enable_original = os.getenv("ENABLE_ORIGINAL_POSTS", "true").lower() == "true"
        self.enable_replies = os.getenv("ENABLE_REPLIES", "true").lower() == "true"
        self.enable_reposts = os.getenv("ENABLE_REPOSTS", "true").lower() == "true"

        # Daily limits (conservative for safety and compliance)
        self.max_daily_original = int(os.getenv("MAX_DAILY_ORIGINAL_POSTS", "4"))
        self.max_daily_replies = int(os.getenv("MAX_DAILY_REPLIES", "14"))
        self.max_daily_reposts = int(os.getenv("MAX_DAILY_REPOSTS", "5"))
        self.max_daily_total = int(os.getenv("MAX_DAILY_TOTAL", "20"))

        # Trial duration enforcement (in hours, e.g. 48)
        self.trial_max_hours = float(os.getenv("TRIAL_MAX_HOURS", "48.0"))

    def check_trial_status(self, trial_start_iso: str) -> Tuple[bool, str]:
        """Verifies if the trial is globally active and within the time window."""
        if not self.trial_enabled:
            return False, "Trial globally disabled via TRIAL_ENABLED=false."

        if trial_start_iso:
            try:
                start_dt = datetime.fromisoformat(trial_start_iso)
                now_dt = datetime.now(timezone.utc)
                elapsed_hours = (now_dt - start_dt).total_seconds() / 3600.0
                if elapsed_hours > self.trial_max_hours:
                    return False, f"Trial duration expired ({elapsed_hours:.1f}h > {self.trial_max_hours}h limit)."
            except Exception:
                pass

        return True, "Active"

    def can_perform_action(self, action_type: str, today_counts: Dict[str, int]) -> Tuple[bool, str]:
        """Evaluates whether an action complies with daily quotas and enabled flags."""
        if today_counts.get("total_actions", 0) >= self.max_daily_total:
            return False, f"Total daily limit reached ({today_counts.get('total_actions')}/{self.max_daily_total})."

        if action_type == "original_post":
            if not self.enable_original:
                return False, "Original posts disabled via ENABLE_ORIGINAL_POSTS=false."
            if today_counts.get("original_posts", 0) >= self.max_daily_original:
                return False, f"Daily original posts limit reached ({today_counts.get('original_posts')}/{self.max_daily_original})."

        elif action_type == "reply":
            if not self.enable_replies:
                return False, "Replies disabled via ENABLE_REPLIES=false."
            if today_counts.get("replies", 0) >= self.max_daily_replies:
                return False, f"Daily replies limit reached ({today_counts.get('replies')}/{self.max_daily_replies})."

        elif action_type in ("repost", "quote_tweet"):
            if not self.enable_reposts:
                return False, "Reposts disabled via ENABLE_REPOSTS=false."
            if today_counts.get("reposts", 0) >= self.max_daily_reposts:
                return False, f"Daily reposts limit reached ({today_counts.get('reposts')}/{self.max_daily_reposts})."

        return True, "Approved"
