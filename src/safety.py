import os
from datetime import datetime, timezone
from typing import Tuple, Dict
from config import CAPS_PER_PLATFORM

class SafetyEngine:
    """
    Enforces rate limits, daily caps, trial time boundaries,
    and platform anti-cannibalization guards.
    """

    def __init__(self):
        # Global enable/disable switch
        self.trial_enabled = os.getenv("TRIAL_ENABLED", "true").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

        # Per-action enable switches
        self.enable_original = os.getenv("ENABLE_ORIGINAL_POSTS", "true").lower() == "true"
        self.enable_replies = os.getenv("ENABLE_REPLIES", "true").lower() == "true"
        self.enable_reposts = os.getenv("ENABLE_REPOSTS", "true").lower() == "true"

        # Platform caps (from config or env overrides)
        self.caps = CAPS_PER_PLATFORM
        self.max_daily_original = self.caps.get("twitter_originals", 4)
        self.max_daily_replies = self.caps.get("twitter_replies", 16)
        self.max_daily_reposts = self.caps.get("twitter_reposts", 5)
        self.max_daily_total = int(os.getenv("MAX_DAILY_TOTAL", "28"))

        # Indefinite 24/7 Autopilot (no expiration limit)
        self.trial_max_hours = float(os.getenv("TRIAL_MAX_HOURS", "0"))

    def check_trial_status(self, trial_start_iso: str) -> Tuple[bool, str]:
        """Verifies if the system is globally active (Permanent Autopilot)."""
        if not self.trial_enabled:
            return False, "System disabled via TRIAL_ENABLED=false."

        # If a positive limit is explicitly provided in env, respect it; otherwise run indefinitely
        if self.trial_max_hours > 0 and trial_start_iso:
            try:
                start_dt = datetime.fromisoformat(trial_start_iso)
                now_dt = datetime.now(timezone.utc)
                elapsed_hours = (now_dt - start_dt).total_seconds() / 3600.0
                if elapsed_hours > self.trial_max_hours:
                    return False, f"Duration expired ({elapsed_hours:.1f}h > {self.trial_max_hours}h limit)."
            except Exception:
                pass

        return True, "Permanent Autopilot Active"

    def can_perform_action(self, action_type: str, today_counts: Dict[str, int]) -> Tuple[bool, str]:
        """Evaluates whether an action complies with daily quotas and anti-cannibalization rules."""
        if self.max_daily_total > 0 and today_counts.get("total_actions", 0) >= self.max_daily_total:
            return False, f"Total daily limit reached ({today_counts.get('total_actions')}/{self.max_daily_total})."

        # Twitter / Omnichannel Original Posts
        if action_type in ("original_post", "post"):
            if not self.enable_original:
                return False, "Original posts disabled via ENABLE_ORIGINAL_POSTS=false."
            limit = self.caps.get("twitter_originals", 4)
            if today_counts.get("original_posts", 0) >= limit:
                return False, f"Daily original posts limit reached ({today_counts.get('original_posts')}/{limit})."

        # Twitter Sniper Replies
        elif action_type == "reply":
            if not self.enable_replies:
                return False, "Replies disabled via ENABLE_REPLIES=false."
            limit = self.caps.get("twitter_replies", 16)
            if today_counts.get("replies", 0) >= limit:
                return False, f"Daily replies limit reached ({today_counts.get('replies')}/{limit})."

        # Quote-Tweets / Reposts
        elif action_type in ("repost", "quote_tweet"):
            if not self.enable_reposts:
                return False, "Reposts disabled via ENABLE_REPOSTS=false."
            limit = self.caps.get("twitter_reposts", 5)
            if today_counts.get("reposts", 0) >= limit:
                return False, f"Daily reposts limit reached ({today_counts.get('reposts')}/{limit})."

        # YouTube Shorts (Anti-cannibalization: max 2/day)
        elif action_type == "youtube":
            limit = self.caps.get("youtube_shorts", 2)
            if today_counts.get("youtube_shorts", 0) >= limit:
                return False, f"YouTube daily cap reached ({today_counts.get('youtube_shorts')}/{limit}) to protect algorithmic impressions."

        # LinkedIn Posts (Strict anti-cannibalization: max 1-2/day)
        elif action_type == "linkedin":
            limit = self.caps.get("linkedin_posts", 1)
            if today_counts.get("linkedin_posts", 0) >= limit:
                return False, f"LinkedIn daily cap reached ({today_counts.get('linkedin_posts')}/{limit}) to prevent reach decay."

        # Instagram Carousels
        elif action_type == "instagram":
            limit = self.caps.get("instagram_carousels", 1)
            if today_counts.get("instagram_carousels", 0) >= limit:
                return False, f"Instagram daily cap reached ({today_counts.get('instagram_carousels')}/{limit})."

        # Dev.to Technical Articles
        elif action_type == "devto":
            limit = self.caps.get("devto_articles", 1)
            if today_counts.get("devto_articles", 0) >= limit:
                return False, f"Dev.to daily cap reached ({today_counts.get('devto_articles')}/{limit}) for 24h freshness."

        # Pinterest Pins
        elif action_type == "pinterest":
            limit = self.caps.get("pinterest_pins", 3)
            if today_counts.get("pinterest_pins", 0) >= limit:
                return False, f"Pinterest daily cap reached ({today_counts.get('pinterest_pins')}/{limit})."

        # Threads
        elif action_type == "threads":
            limit = self.caps.get("threads_posts", 3)
            if today_counts.get("threads_posts", 0) >= limit:
                return False, f"Threads daily cap reached ({today_counts.get('threads_posts')}/{limit})."

        return True, "Approved"
