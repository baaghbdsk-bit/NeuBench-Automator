import sys
import os
import time

import json

import random

import re

from datetime import datetime, timedelta, timezone

from pathlib import Path
from typing import Dict, List, Optional, Any



# Ensure UTF-8 output on Windows consoles

if sys.platform == "win32":

    try:

        sys.stdout.reconfigure(encoding="utf-8")

        sys.stderr.reconfigure(encoding="utf-8")

    except Exception:

        pass



from rich.console import Console



import config

from src.trend_hunter import TrendHunter, LINKEDIN_PILLAR_ROTATION, detect_trend_sensitivity

from src.ai_generator import AIGenerator

from src.twitter_client import TwitterClient

from src.bluesky_client import BlueskyClient

from src.tracker import ActivityTracker

from src.safety import SafetyEngine

from src.linkedin_state import (
    ENGAGEMENT_HISTORY_FILE,
    POST_HISTORY_FILE,
    append_post_entry,
    cadence_slot_key,
    content_hash,
    count_posts_on_date,
    engagement_count_on_date,
    last_post_at,
    linkedin_state_lock,
    load_engagement_history,
    load_post_history,
    post_is_duplicate,
    save_engagement_history,
    save_post_history,
    utc_now_iso,
)
from src.x_state import (
    complete_reservation,
    content_hash as x_content_hash,
    prepare_x_text,
    reserve_original,
    reserve_target,
)
from src.platform_state import (
    complete_platform_action,
    reserve_platform_action,
    stable_hash,
)



console = Console()



# Target high-engagement accounts for explosive reach across Tech, Viral Culture, Finance, and Global Discourse
VIRAL_ACCOUNTS = [
    # Mega-reach Indian National & Viral Culture (Highest impression velocity)
    "narendramodi",
    "AshwiniVaishnaw",
    "IndianTechGuide",
    "peakbengaluru",
    "ANI",
    "NDTV",
    "thetanmay",
    "kunalb11",
    "Zomato",
    "swiggy",
    "Bhaiyyaji_Kahin",
    # Global Tech, AI, & Founders
    "elonmusk",
    "sama",
    "satyanadella",
    "sundarpichai",
    "karpathy",
    "ylecun",
    "mkbhd",
    "levelsio",
    "paulg",
    "naval",
    # Viral Finance, Markets & Breaking News
    "WatcherGuru",
    "unusual_whales",
    "zerohedge",
    "DeItaone",
    "TrungTPhan"
]



class AutomaterEngine:

    def __init__(self, dry_run: bool = False):

        self.hunter = TrendHunter()

        self.ai = AIGenerator()

        self.safety = SafetyEngine()
        self._ai_topic_reservations: set[str] = set()

        

        # Override dry_run if explicitly passed

        if dry_run:

            self.safety.dry_run = True



        self.twitter = TwitterClient(headless=True, dry_run=self.safety.dry_run)

        self.bluesky = BlueskyClient(

            handle=config.BLUESKY_HANDLE,

            app_password=config.BLUESKY_APP_PASSWORD,

            dry_run=self.safety.dry_run

        )

        

        self.history_file = config.BASE_DIR / "post_history.json"

        self.metrics_file = config.BASE_DIR / "trial_metrics.json"

        self.tracker = ActivityTracker(self.metrics_file, self.history_file)
        self.last_x_message = ""

    def _x_guard(self, action_type: str, start_time: float) -> bool:
        """Apply the normal trial and daily-cap policy to direct X actions."""

        trial_start = self.tracker.metrics.get("trial_meta", {}).get("trial_start_utc", "")
        active, reason = self.safety.check_trial_status(trial_start)
        if not active:
            self.last_x_message = reason
            self.tracker.record_event(
                action_type=action_type,
                status="skipped",
                target_identifier="X safety guard",
                skip_or_error_reason=reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return False

        allowed, reason = self.safety.can_perform_action(
            "post" if action_type == "original_post" else action_type,
            self.tracker.get_today_counts(),
        )
        if not allowed:
            self.last_x_message = reason
            self.tracker.record_event(
                action_type=action_type,
                status="skipped",
                target_identifier="X daily cap",
                skip_or_error_reason=reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return False
        return True

    def _reserve_platform(
        self,
        platform: str,
        action_type: str,
        identity: str,
        target: str = "",
        preview: str = "",
    ) -> tuple[Optional[str], str]:
        if self.safety.dry_run:
            return None, "Dry run"
        try:
            return reserve_platform_action(
                self.history_file,
                platform=platform,
                action_type=action_type,
                identity=identity,
                target=target,
                preview=preview,
            )
        except Exception as error:
            return None, f"Could not reserve {platform} state: {error}"

    def _complete_platform(
        self,
        reservation_id: Optional[str],
        *,
        ok: bool,
        unknown: bool = False,
        reason: str = "",
    ) -> str:
        outcome = "success" if ok else "unknown" if unknown else "failed"
        if reservation_id:
            complete_platform_action(
                self.history_file,
                reservation_id,
                outcome=outcome,
                reason=reason,
            )
        return outcome

    def _reserve_ai_topic(self, title: str) -> None:
        if not title or self.safety.dry_run:
            return
        try:
            topics = self.tracker.history.setdefault("posted_ai_topics", [])
            if title not in topics:
                topics.append(title)
                self.tracker.save_history()
                self._ai_topic_reservations.add(title)
        except Exception:
            pass

    def _commit_ai_topic(self, title: str) -> None:
        if title:
            self._ai_topic_reservations.discard(title)

    def _release_ai_topic(self, title: str) -> None:
        if not title or self.safety.dry_run or title not in self._ai_topic_reservations:
            return
        try:
            topics = self.tracker.history.get("posted_ai_topics", [])
            removed = False
            while title in topics:
                topics.remove(title)
                removed = True
            if removed:
                self.tracker.save_history()
            self._ai_topic_reservations.discard(title)
        except Exception:
            pass

    def execute_x_custom_post(self, text: str, media_path: Optional[str] = None) -> bool:
        """Publish a custom X post through the same guarded path as autopilot."""

        start_time = time.time()
        self.last_x_message = ""
        text = prepare_x_text(text)
        if not text:
            self.last_x_message = "X post text is empty."
            self.tracker.record_event(
                action_type="original_post",
                status="skipped",
                target_identifier="X input",
                skip_or_error_reason=self.last_x_message,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return False
        if not self._x_guard("original_post", start_time):
            return False

        target = f"X custom post {x_content_hash(text)[:16]}"
        reservation_id = None
        if not self.safety.dry_run:
            try:
                reservation_id, reason = reserve_original(
                    self.history_file,
                    target_identifier=target,
                    text=text,
                )
            except Exception as error:
                reason = f"Could not reserve X post state: {error}"
            if not reservation_id:
                self.last_x_message = reason
                self.tracker.record_event(
                    action_type="original_post",
                    status="skipped",
                    target_identifier=target,
                    skip_or_error_reason=reason,
                    duration_seconds=time.time() - start_time,
                    is_dry_run=False,
                )
                return False

        try:
            ok = self.twitter.post_tweet(text, media_path=media_path)
        except Exception as error:
            self.twitter.last_outcome_unknown = False
            self.twitter.last_message = f"X post client error: {error}"
            ok = False
        outcome = "success" if ok else "unknown" if self.twitter.last_outcome_unknown else "failed"
        if reservation_id:
            complete_reservation(
                self.history_file,
                reservation_id,
                outcome=outcome,
                target_identifier=target,
                text=text,
                reason=self.twitter.last_message,
            )
        self.last_x_message = self.twitter.last_message or (
            "X post published." if ok else "X post failed."
        )
        self.tracker.record_event(
            action_type="original_post",
            status="success" if ok else "failed",
            target_identifier=target,
            content_preview=text,
            skip_or_error_reason="" if ok else self.last_x_message,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run,
        )
        return ok

    def execute_x_reply(self, tweet_url: str, target_text: str = "Viral debate") -> bool:
        """Publish a direct X reply with target reservation and cap checks."""

        start_time = time.time()
        self.last_x_message = ""
        if not tweet_url:
            self.last_x_message = "X reply URL is empty."
            self.tracker.record_event(
                action_type="reply",
                status="skipped",
                target_identifier="X input",
                skip_or_error_reason=self.last_x_message,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return False
        if not self._x_guard("reply", start_time):
            return False
        try:
            reply_text = self.ai.generate_sniper_reply("tweet_author", target_text or "Viral debate")
        except Exception as error:
            self.last_x_message = f"X reply generation failed: {error}"
            self.tracker.record_event(
                action_type="reply",
                status="failed",
                target_identifier=tweet_url,
                skip_or_error_reason=self.last_x_message,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return False

        reservation_id = None
        if not self.safety.dry_run:
            try:
                reservation_id, reason = reserve_target(
                    self.history_file,
                    action_type="reply",
                    target_identifier=tweet_url,
                    text=reply_text,
                )
            except Exception as error:
                reason = f"Could not reserve X reply state: {error}"
            if not reservation_id:
                self.last_x_message = reason
                self.tracker.record_event(
                    action_type="reply",
                    status="skipped",
                    target_identifier=tweet_url,
                    skip_or_error_reason=reason,
                    duration_seconds=time.time() - start_time,
                    is_dry_run=False,
                )
                return False

        try:
            ok = self.twitter.post_reply(tweet_url, reply_text)
        except Exception as error:
            self.twitter.last_outcome_unknown = False
            self.twitter.last_message = f"X reply client error: {error}"
            ok = False
        outcome = "success" if ok else "unknown" if self.twitter.last_outcome_unknown else "failed"
        if reservation_id:
            complete_reservation(
                self.history_file,
                reservation_id,
                outcome=outcome,
                target_identifier=tweet_url,
                text=reply_text,
                reason=self.twitter.last_message,
            )
        self.last_x_message = self.twitter.last_message or ("X reply published." if ok else "X reply failed.")
        self.tracker.record_event(
            action_type="reply",
            status="success" if ok else "failed",
            target_identifier=tweet_url,
            content_preview=reply_text,
            skip_or_error_reason="" if ok else self.last_x_message,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run,
        )
        return ok

    def execute_x_quote(self, tweet_url: str, target_text: str = "Viral debate") -> bool:
        """Publish a direct X quote-tweet with target reservation and caps."""

        start_time = time.time()
        self.last_x_message = ""
        if not tweet_url:
            self.last_x_message = "X quote-tweet URL is empty."
            self.tracker.record_event(
                action_type="quote_tweet",
                status="skipped",
                target_identifier="X input",
                skip_or_error_reason=self.last_x_message,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return False
        if not self._x_guard("quote_tweet", start_time):
            return False
        try:
            quote_text = self.ai.generate_quote_tweet_commentary("tweet_author", target_text or "Viral debate")
        except Exception as error:
            self.last_x_message = f"X quote-tweet generation failed: {error}"
            self.tracker.record_event(
                action_type="quote_tweet",
                status="failed",
                target_identifier=tweet_url,
                skip_or_error_reason=self.last_x_message,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return False

        reservation_id = None
        if not self.safety.dry_run:
            try:
                reservation_id, reason = reserve_target(
                    self.history_file,
                    action_type="repost",
                    target_identifier=tweet_url,
                    text=quote_text,
                )
            except Exception as error:
                reason = f"Could not reserve X quote-tweet state: {error}"
            if not reservation_id:
                self.last_x_message = reason
                self.tracker.record_event(
                    action_type="quote_tweet",
                    status="skipped",
                    target_identifier=tweet_url,
                    skip_or_error_reason=reason,
                    duration_seconds=time.time() - start_time,
                    is_dry_run=False,
                )
                return False

        try:
            ok = self.twitter.post_quote_tweet(tweet_url, quote_text)
        except Exception as error:
            self.twitter.last_outcome_unknown = False
            self.twitter.last_message = f"X quote-tweet client error: {error}"
            ok = False
        outcome = "success" if ok else "unknown" if self.twitter.last_outcome_unknown else "failed"
        if reservation_id:
            complete_reservation(
                self.history_file,
                reservation_id,
                outcome=outcome,
                target_identifier=tweet_url,
                text=quote_text,
                reason=self.twitter.last_message,
            )
        self.last_x_message = self.twitter.last_message or ("X quote-tweet published." if ok else "X quote-tweet failed.")
        self.tracker.record_event(
            action_type="quote_tweet",
            status="success" if ok else "failed",
            target_identifier=tweet_url,
            content_preview=quote_text,
            skip_or_error_reason="" if ok else self.last_x_message,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run,
        )
        return ok

    def execute_bluesky_custom_post(self, text: str) -> bool:
        """Publish a direct Bluesky draft with the same cap/idempotency policy."""

        start_time = time.time()
        if not text or not str(text).strip():
            self.tracker.record_event(
                action_type="bluesky_post",
                status="skipped",
                target_identifier="Bluesky input",
                skip_or_error_reason="Bluesky post text is empty.",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return False
        allowed, reason = self.safety.can_perform_action("bluesky", self.tracker.get_today_counts())
        if not allowed:
            self.tracker.record_event(
                action_type="bluesky_post",
                status="skipped",
                target_identifier="Bluesky safety guard",
                skip_or_error_reason=reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return False

        identity = f"post:{stable_hash(text)}"
        reservation_id, reservation_reason = self._reserve_platform(
            "bluesky", "post", identity, target="Bluesky direct post", preview=text
        )
        if not self.safety.dry_run and not reservation_id:
            self.tracker.record_event(
                action_type="bluesky_post",
                status="skipped",
                target_identifier="Bluesky direct post",
                content_preview=text,
                skip_or_error_reason=reservation_reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=False,
            )
            return False

        try:
            ok, msg = self.bluesky.post(text)
        except Exception as error:
            ok, msg = False, f"Bluesky client error: {error}"
        self._complete_platform(
            reservation_id,
            ok=ok,
            unknown=getattr(self.bluesky, "last_outcome_unknown", False),
            reason=msg,
        )
        self.tracker.record_event(
            action_type="bluesky_post",
            status="success" if ok else "failed",
            target_identifier="Bluesky direct post",
            content_preview=text,
            skip_or_error_reason="" if ok else msg,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run,
        )
        return ok



    def run_single_cycle(self, force_action: str = "auto") -> bool:

        """

        Executes one verifiable cycle within the safety envelope.

        force_action can be: 'auto', 'post', 'reply', 'repost'

        """

        start_time = time.time()

        start_iso = datetime.now(timezone.utc).isoformat()

        console.print(f"\n[cyan]⏱️  Cycle triggered at {start_iso} (Dry Run: {self.safety.dry_run})[/cyan]")



        # 1. Check Global Trial Status & Window

        trial_start = self.tracker.metrics.get("trial_meta", {}).get("trial_start_utc", "")

        is_active, status_msg = self.safety.check_trial_status(trial_start)

        if not is_active:

            console.print(f"[bold red]⛔ Trial Safety Stop: {status_msg}[/bold red]")

            self.tracker.record_event(

                action_type="lifecycle",

                status="skipped",

                skip_or_error_reason=status_msg,

                duration_seconds=time.time() - start_time,

                is_dry_run=self.safety.dry_run

            )

            return False



        # 2. Get today's quota usage

        today_counts = self.tracker.get_today_counts()

        console.print(

            f"[dim]Today's Verifiable Totals -> Original: {today_counts['original_posts']}/{self.safety.max_daily_original} | "

            f"Replies: {today_counts['replies']}/{self.safety.max_daily_replies} | "

            f"Reposts: {today_counts['reposts']}/{self.safety.max_daily_reposts} | "

            f"Total: {today_counts['total_actions']}/{self.safety.max_daily_total}[/dim]"

        )



        # 3. Determine action type
        valid_forces = ("post", "reply", "repost", "mentions", "debate-sniper", "indian", "bluesky", "bluesky-replies", "linkedin", "linkedin-replies", "linkedin-peers", "omnichannel", "post-all")
        if force_action in valid_forces:
            action_choice = force_action
        else:
            action_choice = "omnichannel"

        # 4. Enforce quota check
        can_proceed, reason = self.safety.can_perform_action(action_choice, today_counts)

        if not can_proceed:

            console.print(f"[yellow]⚠️ Action '{action_choice}' blocked: {reason}[/yellow]")

            # Attempt fallback to alternative action if total limit is not exceeded

            linkedin_only = action_choice in ("linkedin", "linkedin-replies", "linkedin-peers")
            if force_action == "auto" and not linkedin_only and today_counts.get("total_actions", 0) < self.safety.max_daily_total:

                fallbacks = [a for a in ["reply", "post", "repost"] if a != action_choice]

                for fb in fallbacks:

                    fb_ok, _ = self.safety.can_perform_action(fb, today_counts)

                    if fb_ok:

                        console.print(f"[green]Falling back to action: '{fb}'[/green]")

                        action_choice = fb

                        can_proceed = True

                        break



            if not can_proceed:

                self.tracker.record_event(

                    action_type=action_choice,

                    status="skipped",

                    skip_or_error_reason=reason,

                    duration_seconds=time.time() - start_time,

                    is_dry_run=self.safety.dry_run

                )

                return False



        # 5. Dispatch chosen action
        if action_choice in ("omnichannel", "post-all"):
            results = self.run_three_hour_omnichannel_cycle()
            return any(results.values())
        elif action_choice == "mentions":
            return self._execute_x_mentions_replies(start_time)
        elif action_choice == "debate-sniper":
            return self._execute_x_debate_sniper(start_time)
        elif action_choice == "indian":
            return self._execute_indian_engagement(start_time)
        elif action_choice == "reply":
            ok = self._execute_sniper_reply(start_time)
            if not ok:
                if self.twitter.last_outcome_unknown:
                    console.print("[red]X reply outcome is unknown; stopping without retry to prevent a duplicate.[/red]")
                    return False
                console.print("[yellow]Reply mode skipped/failed. Falling back to 𝕏 post...[/yellow]")
                return self._execute_original_post(start_time)
            return ok
        elif action_choice == "repost":
            ok = self._execute_quote_tweet(start_time)
            if not ok:
                if self.twitter.last_outcome_unknown:
                    console.print("[red]X quote-tweet outcome is unknown; stopping without retry to prevent a duplicate.[/red]")
                    return False
                console.print("[yellow]Quote tweet mode skipped/failed. Falling back to 𝕏 post...[/yellow]")
                return self._execute_original_post(start_time)
            return ok
        elif action_choice == "bluesky":
            return self._execute_bluesky_post(start_time)
        elif action_choice == "linkedin":
            return self._execute_linkedin_post(start_time)
        elif action_choice == "linkedin-replies":
            return self._execute_linkedin_comment_replies(start_time)
        elif action_choice == "linkedin-peers":
            return self._execute_linkedin_peer_engagement(start_time)
        elif action_choice == "bluesky-replies":
            return self._execute_bluesky_sniper_replies(start_time)
        else:
            return self._execute_original_post(start_time)



    def _execute_sniper_reply(self, start_time: float) -> bool:

        """Finds a viral account, extracts latest tweet, and replies with high-engagement AI take."""

        console.print("[bold yellow]🎯 Mode: Sniper Reply on Viral Account[/bold yellow]")
        self.twitter.last_outcome_unknown = False

        

        # Sample candidate accounts to try

        candidates = random.sample(VIRAL_ACCOUNTS, min(3, len(VIRAL_ACCOUNTS)))

        tweet_data = {}

        target_account = ""



        for account in candidates:

            console.print(f"[dim]Checking latest tweet from @{account}...[/dim]")

            data = self.twitter.get_latest_tweet_from_account(account)

            url = data.get("tweet_url")

            text = data.get("tweet_text")

            if url and text:

                if url not in self.tracker.history["replied_urls"]:

                    tweet_data = data

                    target_account = account

                    break

                else:

                    console.print(f"[dim]Already replied to {url}. Trying next candidate...[/dim]")



        tweet_url = tweet_data.get("tweet_url")

        tweet_text = tweet_data.get("tweet_text")



        if not tweet_url or not tweet_text:

            console.print("[yellow]Could not find unreplied tweet among candidates. Falling back to Original Hot Take from NeuBench/Trends...[/yellow]")

            return self._execute_original_post(start_time)



        console.print(f"[bold]Target Tweet (@{target_account}):[/bold] {tweet_text[:80]}...")

        self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1

        try:

            reply_content = self.ai.generate_sniper_reply(target_account, tweet_text)

        except Exception as e:

            self.tracker.metrics["lifetime_summary"]["ai_generation_failures"] += 1

            console.print(f"[red]AI Generation Error: {e}[/red]")

            self.tracker.record_event(

                action_type="reply",

                status="failed",

                target_identifier=tweet_url,

                skip_or_error_reason=f"AI generation failed: {e}",

                duration_seconds=time.time() - start_time,

                is_dry_run=self.safety.dry_run

            )

            return False



        console.print(f"[green]Generated Reply Draft:[/green] {reply_content}")



        reservation_id = None
        if not self.safety.dry_run:
            try:
                reservation_id, reservation_reason = reserve_target(
                    self.history_file,
                    action_type="reply",
                    target_identifier=tweet_url,
                    text=reply_content,
                )
            except Exception as error:
                reservation_reason = f"Could not reserve X reply state: {error}"
            if not reservation_id:
                self.tracker.record_event(
                    action_type="reply",
                    status="skipped",
                    target_identifier=tweet_url,
                    skip_or_error_reason=reservation_reason,
                    duration_seconds=time.time() - start_time,
                    is_dry_run=False,
                )
                return False

        try:
            success = self.twitter.post_reply(tweet_url, reply_content)
        except Exception as error:
            self.twitter.last_outcome_unknown = False
            self.twitter.last_message = f"X reply client error: {error}"
            success = False
        outcome = "success" if success else "unknown" if self.twitter.last_outcome_unknown else "failed"
        if reservation_id:
            complete_reservation(
                self.history_file,
                reservation_id,
                outcome=outcome,
                target_identifier=tweet_url,
                text=reply_content,
                reason=self.twitter.last_message,
            )

        status = "success" if success else "failed"

        self.tracker.record_event(

            action_type="reply",

            status=status,

            target_identifier=tweet_url,

            content_preview=reply_content,

            skip_or_error_reason="" if success else self.twitter.last_message or "Playwright selector or network failure",

            duration_seconds=time.time() - start_time,

            is_dry_run=self.safety.dry_run

        )

        if success:

            console.print("[bold green]✅ Successfully sniped reply![/bold green]")

        return success



    def _execute_quote_tweet(self, start_time: float) -> bool:

        """Finds a viral tweet and Quote-Tweets it with commentary ('masala on top')."""

        console.print("[bold blue]🔁 Mode: Quote-Tweet ('Repost with Masala')[/bold blue]")
        self.twitter.last_outcome_unknown = False

        

        candidates = random.sample(VIRAL_ACCOUNTS, min(3, len(VIRAL_ACCOUNTS)))

        tweet_data = {}

        target_account = ""



        for account in candidates:

            console.print(f"[dim]Checking latest tweet from @{account} to quote...[/dim]")

            data = self.twitter.get_latest_tweet_from_account(account)

            url = data.get("tweet_url")

            text = data.get("tweet_text")

            if url and text:

                if url not in self.tracker.history["reposted_urls"]:

                    tweet_data = data

                    target_account = account

                    break

                else:

                    console.print(f"[dim]Already quoted {url}. Trying next candidate...[/dim]")



        tweet_url = tweet_data.get("tweet_url")

        tweet_text = tweet_data.get("tweet_text")



        if not tweet_url or not tweet_text:

            console.print("[yellow]Could not find unquoted tweet among candidates. Falling back to Original Hot Take from NeuBench/Trends...[/yellow]")

            return self._execute_original_post(start_time)



        console.print(f"[bold]Target Tweet (@{target_account}):[/bold] {tweet_text[:80]}...")

        self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1

        try:

            commentary = self.ai.generate_quote_tweet_commentary(target_account, tweet_text)

        except Exception as e:

            self.tracker.metrics["lifetime_summary"]["ai_generation_failures"] += 1

            console.print(f"[red]AI Generation Error: {e}[/red]")

            self.tracker.record_event(

                action_type="quote_tweet",

                status="failed",

                target_identifier=tweet_url,

                skip_or_error_reason=f"AI generation failed: {e}",

                duration_seconds=time.time() - start_time,

                is_dry_run=self.safety.dry_run

            )

            return False



        console.print(f"[green]Generated Quote Draft:[/green] {commentary}")



        reservation_id = None
        if not self.safety.dry_run:
            try:
                reservation_id, reservation_reason = reserve_target(
                    self.history_file,
                    action_type="repost",
                    target_identifier=tweet_url,
                    text=commentary,
                )
            except Exception as error:
                reservation_reason = f"Could not reserve X quote-tweet state: {error}"
            if not reservation_id:
                self.tracker.record_event(
                    action_type="quote_tweet",
                    status="skipped",
                    target_identifier=tweet_url,
                    skip_or_error_reason=reservation_reason,
                    duration_seconds=time.time() - start_time,
                    is_dry_run=False,
                )
                return False

        try:
            success = self.twitter.post_quote_tweet(tweet_url, commentary)
        except Exception as error:
            self.twitter.last_outcome_unknown = False
            self.twitter.last_message = f"X quote-tweet client error: {error}"
            success = False
        outcome = "success" if success else "unknown" if self.twitter.last_outcome_unknown else "failed"
        if reservation_id:
            complete_reservation(
                self.history_file,
                reservation_id,
                outcome=outcome,
                target_identifier=tweet_url,
                text=commentary,
                reason=self.twitter.last_message,
            )

        status = "success" if success else "failed"

        self.tracker.record_event(

            action_type="quote_tweet",

            status=status,

            target_identifier=tweet_url,

            content_preview=commentary,

            skip_or_error_reason="" if success else self.twitter.last_message or "Playwright quote-tweet failure",

            duration_seconds=time.time() - start_time,

            is_dry_run=self.safety.dry_run

        )

        if success:

            console.print("[bold green]✅ Successfully published quote tweet![/bold green]")

        return success




    def _execute_x_mentions_replies(self, start_time: float) -> bool:
        """Checks incoming mentions and replies wittily to build authentic community."""
        console.print("[bold cyan]📬 Mode: 𝕏 Community Mentions & Audience Replies[/bold cyan]")
        mentions = self.twitter.get_incoming_mentions(limit=3)
        if not mentions:
            console.print("[dim]No unreplied mentions found. All caught up![/dim]")
            return True

        replied_count = 0
        for m in mentions:
            tweet_url = m.get("tweet_url")
            author = m.get("author")
            text = m.get("tweet_text")
            if not tweet_url or tweet_url in self.tracker.history.get("replied_urls", []):
                continue

            console.print(f"[bold]Mention from @{author}:[/bold] {text[:70]}...")
            try:
                reply = self.ai.generate_audience_reply(author, text)
            except Exception as e:
                console.print(f"[red]Reply AI error: {e}[/red]")
                continue

            console.print(f"[green]Audience Reply:[/green] {reply}")
            if not self.safety.dry_run:
                ok = self.twitter.post_reply(tweet_url, reply)
                if ok:
                    self.tracker.record_event(
                        action_type="reply",
                        status="success",
                        target_identifier=tweet_url,
                        content_preview=reply,
                        duration_seconds=time.time() - start_time,
                        is_dry_run=False
                    )
                    replied_count += 1
            else:
                print(f"[TwitterClient] [DRY RUN] Would reply to mention from @{author}: {reply}")
                replied_count += 1

        console.print(f"[green]✅ Processed {replied_count} mention reply(ies).[/green]")
        return True

    def _execute_x_debate_sniper(self, start_time: float) -> bool:
        """Searches active debates across 𝕏 and drops a high-signal contrarian comment."""
        console.print("[bold yellow]🔥 Mode: 𝕏 Live Debate Search & Sniper[/bold yellow]")
        topics = self.hunter.get_x_unfiltered_topics()
        topic = random.choice(topics) if topics else {"title": "Tech & AI debates"}
        search_query = topic.get("title", "AI")
        
        results = self.twitter.search_public_tweets(search_query, limit=4)
        target_tweet = None
        for r in results:
            url = r.get("tweet_url")
            if url and url not in self.tracker.history.get("replied_urls", []):
                target_tweet = r
                break

        if not target_tweet:
            console.print("[dim]No unreplied debate tweets found in search. Falling back to account sniper...[/dim]")
            return self._execute_sniper_reply(start_time)

        console.print(f"[bold]Debate Target (@{target_tweet['author']}):[/bold] {target_tweet['tweet_text'][:80]}...")
        reply_take = self.ai.generate_debate_comprehension(search_query, target_tweet["tweet_text"])
        console.print(f"[green]Generated Debate Take:[/green] {reply_take}")

        if not self.safety.dry_run:
            ok = self.twitter.post_reply(target_tweet["tweet_url"], reply_take)
            self.tracker.record_event(
                action_type="reply",
                status="success" if ok else "failed",
                target_identifier=target_tweet["tweet_url"],
                content_preview=reply_take,
                duration_seconds=time.time() - start_time,
                is_dry_run=False
            )
            return ok
        else:
            print(f"[TwitterClient] [DRY RUN] Would reply to debate {target_tweet['tweet_url']}: {reply_take}")
            return True


    def _execute_indian_engagement(self, start_time: float) -> bool:
        """Monitors high-influence Indian accounts, enqueues opportunities, and publishes approved replies."""
        console.print("[bold cyan]🇮🇳 Mode: High-Influence Indian Public Engagement[/bold cyan]")
        from src.indian_influence_engine import IndianEngagementEngine
        engine = IndianEngagementEngine(
            twitter_client=self.twitter,
            ai_generator=self.ai,
            tracker=self.tracker
        )
        # 1. Publish approved opportunity if available
        published = engine.process_approved_queue(dry_run=self.safety.dry_run, max_actions=1)
        if published > 0:
            console.print(f"[bold green]✅ Published {published} queued Indian engagement reply![/bold green]")
            return True

        # 2. Monitor accounts & enqueue fresh opportunities
        discovered = engine.monitor_and_discover_opportunities(sample_size=3)
        return len(discovered) > 0

    def _execute_original_post(self, start_time: float) -> bool:

        """Discovers trending topics and posts a polarizing hot take."""

        console.print("[bold magenta]🚀 Mode: Unfiltered Sarcastic / Hot Take (𝕏)[/bold magenta]")

        # 1. Primary: Discover candidate trends from Trend Intelligence system
        trends = []
        try:
            trends = self.hunter.get_candidate_trends(platform="x", limit=15, include_sensitive=True)
        except Exception as e:
            console.print(f"[dim]Trend Intelligence candidate fetch note: {e}[/dim]")

        # 2. Fallback: If new trend system returns no candidates or fails, use legacy topics
        if not trends:
            trends = self.hunter.get_x_unfiltered_topics()
            if not trends:
                trends = self.hunter.get_casual_topics()

        if not trends:
            console.print("[red]No topics discovered. Skipping...[/red]")
            self.tracker.record_event(
                action_type="original_post",
                status="skipped",
                skip_or_error_reason="Trend discovery returned 0 items",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        # Select an unused, non-sensitive topic for autonomous publishing
        selected_trend = None
        posted_history = set(self.tracker.history.get("posted_tweets", []))
        for t in trends:
            t_title = t.get("title", "")
            if not t_title or t_title in posted_history:
                continue
            # Sensitive topics must NOT be automatically published autonomously
            if t.get("is_sensitive", False):
                console.print(f"[yellow]⚠️ Trend '{t_title}' flagged as sensitive. Skipping autonomous publishing to require manual review.[/yellow]")
                continue
            selected_trend = t
            break

        # Fallback to legacy non-sensitive topics if all candidate trends were used or sensitive
        if not selected_trend:
            legacy_topics = self.hunter.get_x_unfiltered_topics() + self.hunter.get_casual_topics()
            for t in legacy_topics:
                t_title = t.get("title", "")
                if not t_title or t_title in posted_history:
                    continue
                # Enforce sensitivity classification on legacy fallback candidates
                is_sens, _ = detect_trend_sensitivity(t_title, t.get("context", t.get("summary", "")), "breaking_news")
                if is_sens:
                    continue
                selected_trend = t
                break

        # If every candidate and fallback topic is sensitive or used, safely skip autonomous post
        if not selected_trend:
            console.print("[yellow]⚠️ All candidate and fallback topics are flagged as sensitive or already used. Skipping autonomous publishing cycle.[/yellow]")
            self.tracker.record_event(
                action_type="original_post",
                status="skipped",
                skip_or_error_reason="All candidate and fallback topics are sensitive or already posted",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        console.print(f"[bold]𝕏 Topic:[/bold] {selected_trend['title']}")

        # Build enriched context with summary, source, category, and URL
        context_parts = []
        raw_summary = selected_trend.get("summary") or selected_trend.get("context") or ""
        if raw_summary and raw_summary != selected_trend["title"]:
            context_parts.append(raw_summary)
        source_name = selected_trend.get("source")
        if source_name:
            context_parts.append(f"Source: {source_name}")
        cat = selected_trend.get("category")
        if cat:
            context_parts.append(f"Category: {cat}")
        url = selected_trend.get("url")
        if url:
            context_parts.append(f"URL: {url}")
        enriched_context = " | ".join(context_parts) if context_parts else raw_summary

        self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1

        try:
            hot_take = self.ai.generate_hot_take(
                selected_trend["title"],
                enriched_context
            )
        except Exception as e:

            self.tracker.metrics["lifetime_summary"]["ai_generation_failures"] += 1

            console.print(f"[red]AI Generation Error: {e}[/red]")

            self.tracker.record_event(

                action_type="original_post",

                status="failed",

                target_identifier=selected_trend["title"],

                skip_or_error_reason=f"AI generation failed: {e}",

                duration_seconds=time.time() - start_time,

                is_dry_run=self.safety.dry_run

            )

            return False



        console.print(f"[green]Generated Hot Take Draft:[/green] {hot_take}")



        # Text-only tweets on X: visual attachments removed completely for clean, native engagement
        twitter_media = None

        # 1. Post to X (Twitter) - Clean text-only tweet
        reservation_id = None
        if not self.safety.dry_run:
            try:
                reservation_id, reservation_reason = reserve_original(
                    self.history_file,
                    target_identifier=selected_trend["title"],
                    text=hot_take,
                )
            except Exception as error:
                reservation_reason = f"Could not reserve X post state: {error}"
            if not reservation_id:
                self.tracker.record_event(
                    action_type="original_post",
                    status="skipped",
                    target_identifier=selected_trend["title"],
                    skip_or_error_reason=reservation_reason,
                    duration_seconds=time.time() - start_time,
                    is_dry_run=False,
                )
                return False

        try:
            success = self.twitter.post_tweet(hot_take, media_path=twitter_media)
        except Exception as error:
            self.twitter.last_outcome_unknown = False
            self.twitter.last_message = f"X post client error: {error}"
            success = False
        outcome = "success" if success else "unknown" if self.twitter.last_outcome_unknown else "failed"
        if reservation_id:
            complete_reservation(
                self.history_file,
                reservation_id,
                outcome=outcome,
                target_identifier=selected_trend["title"],
                text=hot_take,
                reason=self.twitter.last_message,
            )
        status = "success" if success else "failed"
        self.last_x_message = self.twitter.last_message or (
            "X post published." if success else "X post failed."
        )
        self.tracker.record_event(
            action_type="original_post",
            status=status,
            target_identifier=selected_trend["title"],
            content_preview=hot_take,
            skip_or_error_reason="" if success else self.twitter.last_message or "Playwright compose failure",
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )
        if success:
            console.print("[bold green]✅ Successfully published tweet on 𝕏![/bold green]")
            try:
                self.tracker.history.setdefault("posted_tweets", []).append(selected_trend["title"])
                self.tracker.save_history()
            except Exception:
                pass
            return True
        else:
            console.print("[yellow]⚠️ 𝕏 post could not be published.[/yellow]")
            return False
    def _execute_bluesky_post(self, start_time: float) -> bool:
        """Generates a developer-focused Bluesky take from a trending topic and publishes it."""
        console.print("[bold cyan]🦋 Mode: Bluesky Auto Post (AT Protocol)[/bold cyan]")

        # Cross-platform deduplication across Bluesky, LinkedIn, and X
        used_topics = set()
        for t in self.tracker.history.get("posted_tweets", []):
            clean = re.sub(r"^(bsky|th|li|rd):\s*", "", str(t)).strip().lower()
            if clean:
                used_topics.add(clean)
        for t in self.tracker.history.get("posted_ai_topics", []):
            clean = str(t).strip().lower()
            if clean:
                used_topics.add(clean)
        try:
            from src.linkedin_state import load_post_history, POST_HISTORY_FILE
            for p in load_post_history(POST_HISTORY_FILE).get("posts", []):
                t = str(p.get("title", "")).strip().lower()
                if t:
                    used_topics.add(t)
        except Exception:
            pass

        bsky_cycle = len([e for e in self.tracker.metrics.get("recent_events", []) if "bluesky" in e.get("action_type", "")])
        available_concepts = [c for c in self.hunter.get_educational_concepts() if str(c.get("title", "")).strip().lower() not in used_topics]
        
        # Candidate live trends
        candidate_trends = [t for t in self.hunter.get_linkedin_topics() if str(t.get("title", "")).strip().lower() not in used_topics]

        media_path = None
        concept = None
        selected_trend = None

        if available_concepts and (bsky_cycle % 2 == 1 or not candidate_trends):
            concept = available_concepts[0]
            selected_trend = {"title": concept["title"], "summary": concept.get("golden_rule", "")}
            console.print(f"[bold]🎓 Educational Concept (Bluesky):[/bold] {concept['title']}")
            self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1
            try:
                bsky_take = self.ai.generate_bluesky_concept_post(concept)
                media_path = None
            except Exception as e:
                self.tracker.metrics["lifetime_summary"]["ai_generation_failures"] += 1
                console.print(f"[red]AI Generation Error: {e}[/red]")
                return False
        else:
            trends = candidate_trends or self.hunter.get_linkedin_topics()
            if not trends:
                console.print("[red]No trends discovered. Skipping Bluesky post...[/red]")
                return False
            selected_trend = trends[0]
            self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1
            bsky_take = self.ai.generate_bluesky_take(selected_trend["title"], selected_trend.get("summary", ""))

        console.print(f"[green]Generated Bluesky Draft:[/green] {bsky_take}")

        if not self.safety.dry_run and not self.bluesky.is_configured():
            console.print("[yellow]⚠️ Bluesky credentials not configured. Skipping publish.[/yellow]")
            self.tracker.record_event(
                action_type="bluesky_post",
                status="skipped",
                target_identifier=selected_trend["title"],
                content_preview=bsky_take,
                skip_or_error_reason="Bluesky credentials not configured",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        identity = f"post:{stable_hash(bsky_take)}"
        reservation_id, reservation_reason = self._reserve_platform(
            "bluesky",
            "post",
            identity,
            target=selected_trend["title"],
            preview=bsky_take,
        )
        if not self.safety.dry_run and not reservation_id:
            self.tracker.record_event(
                action_type="bluesky_post",
                status="skipped",
                target_identifier=selected_trend["title"],
                content_preview=bsky_take,
                skip_or_error_reason=reservation_reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=False,
            )
            return False

        # Clean text-only post on Bluesky: visual media removed completely for maximum quality & speed
        media_path = None

        try:
            ok, msg = self.bluesky.post(bsky_take, media_path=media_path)
        except Exception as error:
            ok, msg = False, f"Bluesky client error: {error}"
        outcome = self._complete_platform(
            reservation_id,
            ok=ok,
            unknown=getattr(self.bluesky, "last_outcome_unknown", False),
            reason=msg,
        )
        status = "success" if ok else "failed"
        self.tracker.record_event(
            action_type="bluesky_post",
            status=status,
            target_identifier=selected_trend["title"],
            content_preview=bsky_take,
            skip_or_error_reason="" if ok else msg,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )

        if ok:
            console.print(f"[bold cyan]✅ {msg}[/bold cyan]")
            try:
                self.tracker.history.setdefault("posted_tweets", []).append(f"bsky:{selected_trend['title']}")
                self.tracker.save_history()
            except Exception:
                pass
        else:
            console.print(f"[red]Bluesky publish failed: {msg}[/red]")

        return ok


    def execute_linkedin_custom_post(self, text: str) -> bool:
        """Publish dashboard/CLI text through the same LinkedIn safety policy."""

        return self._execute_linkedin_post(time.time(), custom_text=text)


    def _execute_linkedin_post(self, start_time: float, custom_text: Optional[str] = None) -> bool:
        """Publish one current AI/tech topic with cadence and durable dedupe guards."""

        console.print("[bold blue]💼 Mode: Dedicated LinkedIn Post (Standalone)[/bold blue]")

        if not config.LINKEDIN_ENABLED:
            console.print("[yellow]LinkedIn automation is disabled via LINKEDIN_ENABLED. Skipping.[/yellow]")
            return False

        from src.linkedin_automater import LinkedInAutomater

        automater = LinkedInAutomater(headless=True, dry_run=self.safety.dry_run)
        with linkedin_state_lock():
            post_state = load_post_history(POST_HISTORY_FILE)
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            max_li = config.CAPS_PER_PLATFORM.get("linkedin_posts", 8)
            event_count = sum(
                1
                for event in self.tracker.metrics.get("recent_events", [])
                if event.get("timestamp", "").startswith(today_str)
                and event.get("status") == "success"
                and not event.get("is_dry_run", False)
                and event.get("action_type") == "linkedin_post"
            )
            today_li = max(count_posts_on_date(post_state, today_str), event_count)

            # Dry runs are previews and never reserve a cadence slot or history entry.
            if not self.safety.dry_run:
                # LinkedIn daily cap and cadence guard removed per user configuration (deduplication still active)
                pass

            has_linkedin_api = bool(
                os.getenv("LINKEDIN_ACCESS_TOKEN")
                and os.getenv("LINKEDIN_PERSON_URN")
            )
            if not self.safety.dry_run and not has_linkedin_api and not automater.is_session_available():
                reason = "LinkedIn session/API credentials are not authenticated"
                console.print(f"[yellow]⚠️ {reason}. Skipping.[/yellow]")
                self.tracker.record_event(
                    action_type="linkedin_post",
                    status="skipped",
                    target_identifier="LinkedIn session",
                    skip_or_error_reason=reason,
                    duration_seconds=time.time() - start_time,
                    is_dry_run=False,
                )
                return False

            selected_trend: Dict[str, Any]
            li_text = ""
            carousel_plan: Optional[Dict[str, Any]] = None
            if custom_text and custom_text.strip():
                li_text = custom_text.strip()
                first_line = li_text.splitlines()[0].strip() if li_text else ""
                clean_title = re.sub(r'^[#*\-•\s]+', '', first_line)[:60].strip()
                selected_trend = {
                    "title": clean_title if len(clean_title) >= 10 else f"Custom LinkedIn post {content_hash(li_text)[:16]}",
                    "summary": li_text[:300],
                    "company": "NeuBench",
                    "url": "",
                }
                if post_is_duplicate(post_state, title=selected_trend["title"], content=li_text):
                    reason = "This LinkedIn post body was already published recently"
                    console.print(f"[yellow]♻️ {reason}. Skipping.[/yellow]")
                    self.tracker.record_event(
                        action_type="linkedin_post",
                        status="skipped",
                        target_identifier="LinkedIn dedupe",
                        skip_or_error_reason=reason,
                        duration_seconds=time.time() - start_time,
                        is_dry_run=self.safety.dry_run,
                    )
                    return False
            elif custom_text is not None:
                reason = "Custom LinkedIn text is empty"
                self.tracker.record_event(
                    action_type="linkedin_post",
                    status="skipped",
                    target_identifier="LinkedIn input",
                    skip_or_error_reason=reason,
                    duration_seconds=time.time() - start_time,
                    is_dry_run=self.safety.dry_run,
                )
                return False
            else:
                # Robust cross-platform deduplication
                used_li = set()
                for entry in post_state.get("posts", []):
                    t = str(entry.get("title", "")).strip().lower()
                    if t:
                        used_li.add(t)
                for entry in self.tracker.history.get("posted_tweets", []):
                    clean = re.sub(r"^(bsky|th|li|rd):\s*", "", str(entry)).strip().lower()
                    if clean:
                        used_li.add(clean)
                for entry in self.tracker.history.get("posted_ai_topics", []):
                    clean = str(entry).strip().lower()
                    if clean:
                        used_li.add(clean)

                total_li = len(post_state.get("posts", [])) + len([e for e in self.tracker.metrics.get("recent_events", []) if "linkedin" in e.get("action_type", "")])
                pillar = LINKEDIN_PILLAR_ROTATION[total_li % len(LINKEDIN_PILLAR_ROTATION)]
                console.print(f"[bold]LinkedIn Pillar:[/bold] {pillar}")

                # Candidate topics across 3 streams: comparisons, deep-dive concepts, and live trends
                available_comparisons = [
                    c for c in getattr(self.hunter, "get_comparison_topics", lambda: [])()
                    if str(c.get("title", "")).strip().lower() not in used_li
                ]
                available_concepts = [
                    c for c in self.hunter.get_educational_concepts()
                    if str(c.get("title", "")).strip().lower() not in used_li
                ]

                # Candidate live trends (TrendHunter cache, daily papers, benchmarks)
                trends = self.hunter.get_candidate_trends(platform="linkedin")
                if not trends:
                    trends = self.hunter.get_linkedin_topics(pillar=pillar)
                if pillar != "NEWS":
                    seen_titles = {str(item.get("title", "")).strip().lower() for item in trends}
                    for extra in self.hunter.get_linkedin_topics(pillar="NEWS"):
                        if str(extra.get("title", "")).strip().lower() not in seen_titles:
                            trends.append(extra)
                if not trends:
                    trends = self.hunter.get_linkedin_topics()

                available_trends = [
                    trend for trend in trends
                    if str(trend.get("title", "")).strip().lower() not in used_li
                    and not post_is_duplicate(post_state, title=str(trend.get("title", "")), url=str(trend.get("url", "")))
                ]

                media_path = None
                media_title = ""
                first_comm = None
                selected_trend = {}
                carousel_plan = None
                li_text = ""

                # Intelligent 3-way rotation:
                # 0 -> Comparative Architecture (A vs B)
                # 1 -> Comprehensive Handwritten Study Notes (Engineering Deep Dive)
                # 2 -> Live Trends / News / Benchmarks
                rotation_slot = total_li % 3

                from src.ai_generator import select_linkedin_content_format, validate_educational_plan

                # Strategy selection with graceful cascade
                candidate_attempts = []
                if rotation_slot == 0 and available_comparisons:
                    candidate_attempts.append(("comparison", available_comparisons[0]))
                elif rotation_slot == 1 and available_concepts:
                    candidate_attempts.append(("concept", available_concepts[0]))

                # Add remaining categories as fallbacks
                if available_comparisons and ("comparison", available_comparisons[0]) not in candidate_attempts:
                    candidate_attempts.append(("comparison", available_comparisons[0]))
                if available_concepts and ("concept", available_concepts[0]) not in candidate_attempts:
                    candidate_attempts.append(("concept", available_concepts[0]))
                for trend in available_trends:
                    candidate_attempts.append(("trend", trend))

                for mode, item in candidate_attempts:
                    title = str(item.get("title", "")).strip()
                    summary = str(item.get("summary") or item.get("golden_rule") or "").strip()
                    self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1

                    try:
                        if mode == "comparison":
                            console.print(f"[bold]⚖️ LinkedIn Comparison Carousel (A vs B):[/bold] {title}")
                            plan = self.ai.generate_comparison_plan(title, summary)
                        elif mode == "concept":
                            console.print(f"[bold]🎓 LinkedIn Educational Notes (Deep Dive):[/bold] {title}")
                            plan = self.ai.generate_educational_notes_plan(item)
                        else:
                            # Trend format classification
                            fmt = select_linkedin_content_format(title, summary)
                            if fmt == "comparison_carousel":
                                console.print(f"[bold]⚖️ LinkedIn Trend (Versus Format):[/bold] {title}")
                                plan = self.ai.generate_comparison_plan(title, summary)
                            elif fmt == "handwritten_notes":
                                console.print(f"[bold]🎓 LinkedIn Trend (Study Notes Format):[/bold] {title}")
                                plan = self.ai.generate_educational_notes_plan({"title": title, "summary": summary, "pillar": str(item.get("pillar") or pillar)})
                            else:
                                console.print(f"[bold]LinkedIn Topic (Professional Carousel):[/bold] {title}")
                                recent_hooks = [
                                    (str(entry.get("content") or "").splitlines()[0][:80] if entry.get("content") else str(entry.get("title", ""))[:80])
                                    for entry in post_state.get("posts", [])[-6:]
                                ]
                                plan = self.ai.generate_linkedin_carousel_plan(
                                    title,
                                    summary,
                                    pillar=str(item.get("pillar") or pillar),
                                    recent_hooks=[h for h in recent_hooks if h],
                                )

                        candidate_text = str(plan.get("post_text") or "").strip()
                        if candidate_text:
                            # Validate plan density
                            is_valid, validation_msg = validate_educational_plan(plan)
                            if not is_valid:
                                console.print(f"[yellow]Plan validation warning: {validation_msg} (using with fallback normalization)[/yellow]")
                            selected_trend = {"title": title, "summary": summary, "url": str(item.get("url") or "")}
                            li_text = candidate_text
                            carousel_plan = plan
                            media_path = None
                            first_comm = plan.get("first_comment") or "⚡ Benchmarking 266+ LLMs, latency, and systems architectures live on: https://app.neubench.workers.dev"
                            break
                    except Exception as gen_err:
                        console.print(f"[yellow]Failed generation for '{title}' ({mode}): {gen_err}[/yellow]")
                        continue

                if not selected_trend:
                    console.print("[yellow]All LinkedIn candidate topics and concepts posted recently or failed generation.[/yellow]")
                    return False

            if not media_path and carousel_plan:
                tags = [
                    str(tag).strip()
                    for tag in carousel_plan.get("hashtags", [])
                    if str(tag).strip()
                ]
                if tags and "#" not in li_text[-200:]:
                    li_text = f"{li_text.rstrip()}\n\n{' '.join(tags[:5])}"

                try:
                    from src.linkedin_visuals import render_linkedin_carousel, render_linkedin_hero
                except Exception as import_error:
                    console.print(f"[yellow]LinkedIn visual renderer unavailable: {import_error}[/yellow]")
                    render_linkedin_carousel = None
                    render_linkedin_hero = None

                if render_linkedin_carousel:
                    try:
                        assets = render_linkedin_carousel(carousel_plan)
                        media_path = assets["pdf_path"]
                        media_title = str(
                            carousel_plan.get("cover", {}).get("headline") or selected_trend["title"]
                        )[:100]
                        render_linkedin_hero(carousel_plan, base_name=assets["base"])
                        console.print(
                            f"[bold magenta]🎞️ LinkedIn carousel ready: {media_path} "
                            f"({assets.get('slide_count', 0)} slides)[/bold magenta]"
                        )
                    except Exception as error:
                        console.print(
                            f"[yellow]Carousel render failed ({error}); falling back to hero image.[/yellow]"
                        )
                        try:
                            media_path = render_linkedin_hero(carousel_plan)
                            media_title = str(
                                carousel_plan.get("cover", {}).get("headline") or selected_trend["title"]
                            )[:100]
                        except Exception as hero_error:
                            console.print(f"[dim]Hero render failed too: {hero_error}[/dim]")
                            media_path = None

            console.print(f"[green]Generated LinkedIn Draft:[/green] {li_text[:120]}...")

            first_comm = None
            if carousel_plan:
                first_comm = str(carousel_plan.get("first_comment") or "").strip()
                site = str((carousel_plan.get("cta") or {}).get("website") or "app.neubench.workers.dev").strip()
                if first_comm and site and "http" not in first_comm:
                    first_comm = f"{first_comm}\n\n{site if site.startswith('http') else 'https://' + site}"
                if first_comm:
                    console.print(
                        f"[dim]💬 First-comment fallback ready (LinkedIn may skip it on personal tokens):[/dim] "
                        f"{first_comm[:100]}..."
                    )

            ok, msg = automater.post(
                li_text,
                image_path=media_path,
                first_comment=first_comm,
                media_title=media_title or None,
            )
            now_iso = utc_now_iso()
            post_urn_match = re.search(r"urn:li:[^\s,)]+", msg or "")
            post_urn = post_urn_match.group(0) if post_urn_match else ""

            if ok and not self.safety.dry_run:
                try:
                    append_post_entry(
                        post_state,
                        title=selected_trend["title"],
                        url=selected_trend.get("url", ""),
                        content=li_text,
                        status="success",
                        posted_at=now_iso,
                        post_urn=post_urn,
                    )
                    save_post_history(post_state, POST_HISTORY_FILE)
                    self.tracker.history.setdefault("posted_tweets", []).append(f"li:{selected_trend['title']}")
                    self.tracker.save_history()
                except Exception as error:
                    console.print(f"[red]LinkedIn history persistence error after successful post: {error}[/red]")
            elif not ok and not self.safety.dry_run and getattr(automater, "last_post_outcome_unknown", False):
                # A timeout after submission may mean LinkedIn accepted the post. Reserve
                # the topic/body so the next CI runner cannot publish a duplicate.
                try:
                    append_post_entry(
                        post_state,
                        title=selected_trend["title"],
                        url=selected_trend.get("url", ""),
                        content=li_text,
                        status="unknown",
                        posted_at=now_iso,
                    )
                    save_post_history(post_state, POST_HISTORY_FILE)
                except Exception as error:
                    console.print(f"[red]Unknown-outcome history persistence error: {error}[/red]")

            status = "success" if ok else "failed"
            self.tracker.record_event(
                action_type="linkedin_post",
                status=status,
                target_identifier="LinkedIn B2B",
                content_preview=li_text,
                skip_or_error_reason="" if ok else msg,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )

            if ok:
                console.print(f"[bold blue]✅ {msg}[/bold blue]")
            else:
                console.print(f"[red]LinkedIn publish failed: {msg}[/red]")
            return ok




    def run_three_hour_omnichannel_cycle(self) -> Dict[str, bool]:
        """
        Executes unified 3-hour broadcast cycle across all 3 active platforms:
        1. 𝕏 (Twitter): Unfiltered, sarcastic, roasting, or hot debate take (or sniper reply).
        2. LinkedIn: Authoritative educational article with 1080x1080 looping GIF.
        3. Bluesky: High-signal technical summary with matching 1080x1080 looping GIF.
        """
        start_time = time.time()
        start_iso = datetime.now(timezone.utc).isoformat()
        console.print(f"\n[bold cyan]🚀 Starting 3-Hour Broadcast Cycle at {start_iso} (Dry Run: {self.safety.dry_run})...[/bold cyan]")
        
        results = {"x": False, "linkedin": False, "bluesky": False}

        # 1. 𝕏 (Twitter) - Unfiltered, Sarcastic, Roasting Hot Take
        try:
            console.print("[bold magenta]🐦 1. Dispatching to 𝕏 (Unfiltered Sarcastic / Hot Debate Take)...[/bold magenta]")
            results["x"] = self._execute_original_post(time.time())
        except Exception as e:
            console.print(f"[red]𝕏 Error: {e}[/red]")

        # 2. LinkedIn - Professional Educational Article with Looping GIF
        try:
            console.print("[bold blue]💼 2. Dispatching to LinkedIn (Professional Educational Article + Looping GIF)...[/bold blue]")
            results["linkedin"] = self._execute_linkedin_post(time.time())
        except Exception as e:
            console.print(f"[red]LinkedIn Error: {e}[/red]")

        # 3. Bluesky - Professional Technical Summary with Matching Looping GIF
        try:
            console.print("[bold cyan]🦋 3. Dispatching to Bluesky (Professional Summary + Looping GIF)...[/bold cyan]")
            results["bluesky"] = self._execute_bluesky_post(time.time())
        except Exception as e:
            console.print(f"[red]Bluesky Error: {e}[/red]")

        duration = round(time.time() - start_time, 1)
        console.print(f"\n[bold green]🏁 3-Hour Broadcast Cycle Complete in {duration}s! Results: {results}[/bold green]\n")
        return results

    def _execute_linkedin_comment_replies(self, start_time: float) -> bool:
        """Scans recent LinkedIn posts and replies professionally to incoming comments."""
        console.print("[bold blue]💬 Mode: LinkedIn Comment Replies (Professional B2B)[/bold blue]")
        from src.linkedin_automater import LinkedInAutomater
        automater = LinkedInAutomater(headless=True, dry_run=self.safety.dry_run)
        with linkedin_state_lock():
            engagements = load_engagement_history(ENGAGEMENT_HISTORY_FILE)
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            max_daily = config.CAPS_PER_PLATFORM.get("linkedin_peer_comments", 10)
            remaining = max_daily - engagement_count_on_date(engagements, today_str)
            if remaining <= 0:
                msg = f"LinkedIn engagement daily cap reached ({max_daily}/{max_daily})."
                self.tracker.record_event(
                    action_type="linkedin_reply",
                    status="skipped",
                    target_identifier="LinkedIn Comments",
                    skip_or_error_reason=msg,
                    duration_seconds=time.time() - start_time,
                    is_dry_run=self.safety.dry_run,
                )
                return False

            if not self.safety.dry_run and not automater.is_browser_session_available():
                msg = "LinkedIn browser session not authenticated for comment replies."
                console.print(f"[yellow]{msg}[/yellow]")
                self.tracker.record_event(
                    action_type="linkedin_reply",
                    status="skipped",
                    target_identifier="LinkedIn session",
                    skip_or_error_reason=msg,
                    duration_seconds=time.time() - start_time,
                    is_dry_run=False,
                )
                return False

            already_replied = {
                entry.get("key")
                for entry in engagements
                if entry.get("type") in {"own_reply", "reply"} and entry.get("key")
            }
            replied_ids: List[str] = []
            count, msg = automater.reply_to_own_post_comments(
                max_replies=min(remaining, 5),
                already_replied=already_replied,
                replied_ids=replied_ids,
            )
            now_iso = utc_now_iso()
            new_entries = [
                {"key": key, "type": "own_reply", "ts": now_iso}
                for key in replied_ids
            ]
            if new_entries and not self.safety.dry_run:
                engagements.extend(new_entries)
                save_engagement_history(engagements, ENGAGEMENT_HISTORY_FILE)

            actual = len(new_entries)
            console.print(f"[bold green]✅ {msg}[/bold green]")
            self.tracker.record_event(
                action_type="linkedin_reply",
                status="success" if actual > 0 else "skipped",
                target_identifier="LinkedIn Comments",
                content_preview=msg,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return actual > 0

    def _execute_linkedin_peer_engagement(self, start_time: float) -> bool:
        """Comments on viral LinkedIn posts and replies to suitable questions, within a daily cap."""
        console.print("[bold blue]🌐 Mode: LinkedIn Viral Engagement (Comments + Replies)[/bold blue]")
        if not config.LINKEDIN_ENABLED:
            console.print("[yellow]LinkedIn automation is disabled via LINKEDIN_ENABLED. Skipping.[/yellow]")
            return False

        from src.linkedin_automater import LinkedInAutomater
        automater = LinkedInAutomater(headless=True, dry_run=self.safety.dry_run)
        with linkedin_state_lock():
            engagements = load_engagement_history(ENGAGEMENT_HISTORY_FILE)
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            today_count = engagement_count_on_date(engagements, today_str)
            max_daily = config.CAPS_PER_PLATFORM.get("linkedin_peer_comments", 10)
            remaining = max_daily - today_count
            if remaining <= 0:
                msg = f"LinkedIn engagement daily cap reached ({today_count}/{max_daily})."
                console.print(f"[yellow]{msg} Skipping.[/yellow]")
                self.tracker.record_event(
                    action_type="linkedin_peer_comment",
                    status="skipped",
                    target_identifier="LinkedIn daily cap",
                    skip_or_error_reason=msg,
                    duration_seconds=time.time() - start_time,
                    is_dry_run=self.safety.dry_run,
                )
                return False

            if not self.safety.dry_run and not automater.is_browser_session_available():
                msg = "LinkedIn browser session not authenticated for engagement."
                console.print(f"[yellow]{msg} Skipping.[/yellow]")
                self.tracker.record_event(
                    action_type="linkedin_peer_comment",
                    status="skipped",
                    target_identifier="LinkedIn session",
                    skip_or_error_reason=msg,
                    duration_seconds=time.time() - start_time,
                    is_dry_run=False,
                )
                return False

            already_commented = {
                entry.get("key")
                for entry in engagements
                if entry.get("type") == "comment" and entry.get("key")
            }
            already_replied = {
                entry.get("key")
                for entry in engagements
                if entry.get("type") in {"own_reply", "reply"} and entry.get("key")
            }
            commented_ids: List[str] = []
            replied_ids: List[str] = []
            messages: List[str] = []

            # Answer comments on our own posts first, then spend any remaining
            # budget on high-signal peer comments/replies.
            own_count, own_msg = automater.reply_to_own_post_comments(
                max_replies=min(remaining, 2),
                already_replied=already_replied,
                replied_ids=replied_ids,
            )
            if own_msg:
                messages.append(own_msg)
            remaining -= len(replied_ids)

            if remaining > 0:
                _, peer_msg = automater.engage_with_peer_posts(
                    max_comments=min(remaining, 2),
                    max_replies=min(remaining, 1),
                    max_total=remaining,
                    already_commented=already_commented,
                    already_replied=already_replied,
                    commented_ids=commented_ids,
                    replied_ids=replied_ids,
                )
                if peer_msg:
                    messages.append(peer_msg)

            now_iso = utc_now_iso()
            # The first reply IDs are own-post replies; preserve their type.
            own_reply_count = min(own_count, len(replied_ids))
            new_entries = [
                {"key": key, "type": "own_reply", "ts": now_iso}
                for key in replied_ids[:own_reply_count]
            ] + [
                {"key": key, "type": "reply", "ts": now_iso}
                for key in replied_ids[own_reply_count:]
            ] + [
                {"key": key, "type": "comment", "ts": now_iso}
                for key in commented_ids
            ]

            if new_entries and not self.safety.dry_run:
                engagements.extend(new_entries)
                save_engagement_history(engagements, ENGAGEMENT_HISTORY_FILE)

            actual = len(new_entries)
            msg = " ".join(messages) or "No suitable LinkedIn engagement targets found."
            console.print(f"[bold green]✅ {msg}[/bold green]")
            self.tracker.record_event(
                action_type="linkedin_peer_comment",
                status="success" if actual > 0 else "skipped",
                target_identifier="LinkedIn Viral Engagement",
                content_preview=msg,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return actual > 0


    def _execute_bluesky_sniper_replies(self, start_time: float) -> bool:
        """Finds discussions across tech and AI engineering on Bluesky and posts professional, insightful replies."""
        console.print("[bold cyan]🌌 Mode: Bluesky Professional Technical Replies[/bold cyan]")
        if not self.bluesky.is_configured():
            console.print("[yellow]Bluesky credentials not configured. Skipping.[/yellow]")
            return False
        
        search_queries = ["AI benchmark OR LLM", "machine learning architecture", "inference latency", "open source model", "deep learning"]
        q = random.choice(search_queries)
        posts = self.bluesky.search_viral_posts(query=q, limit=6)
        if not posts:
            console.print(f"[yellow]No relevant technical Bluesky posts found for '{q}'. Falling back...[/yellow]")
            return False
        target_p = random.choice(posts[:3])
        author = target_p.get("author", {}).get("handle", "user")
        text = target_p.get("record", {}).get("text", "")
        reply_take = self.ai.generate_bluesky_sniper_reply(author, text)
        ok, msg = self.bluesky.reply(target_p, reply_take)
        if ok:
            console.print(f"[bold green]✅ Replied professionally on Bluesky to @{author}: {reply_take[:60]}...[/bold green]")
            self.tracker.record_event(
                action_type="bluesky_reply",
                status="success",
                target_identifier=f"@{author}",
                content_preview=reply_take,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return True
        return False

