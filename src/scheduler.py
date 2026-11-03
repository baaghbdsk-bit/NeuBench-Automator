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

from src.trend_hunter import TrendHunter

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
        valid_forces = ("post", "reply", "repost", "bluesky", "bluesky-replies", "linkedin", "linkedin-replies", "linkedin-peers", "threads", "threads-replies", "omnichannel", "post-all", "youtube", "instagram", "devto", "pinterest")
        if force_action in valid_forces:
            action_choice = force_action
        else:
            action_choice = self._resolve_algorithmic_action(today_counts)

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
        if action_choice == "reply":
            ok = self._execute_sniper_reply(start_time)
            if not ok:
                if self.twitter.last_outcome_unknown:
                    console.print("[red]X reply outcome is unknown; stopping without retry to prevent a duplicate.[/red]")
                    return False
                console.print("[yellow]Reply mode skipped/failed. Falling back to Omnichannel broadcast...[/yellow]")
                return self._execute_original_post(start_time)
            return ok
        elif action_choice == "repost":
            ok = self._execute_quote_tweet(start_time)
            if not ok:
                if self.twitter.last_outcome_unknown:
                    console.print("[red]X quote-tweet outcome is unknown; stopping without retry to prevent a duplicate.[/red]")
                    return False
                console.print("[yellow]Quote tweet mode skipped/failed. Falling back to Omnichannel broadcast...[/yellow]")
                return self._execute_original_post(start_time)
            return ok
        elif action_choice == "bluesky":
            return self._execute_bluesky_post(start_time)
        elif action_choice == "linkedin":
            return self._execute_linkedin_post(start_time)
        elif action_choice == "threads":
            # A direct Threads request must never silently publish an X post
            # when Threads is unavailable or its result is uncertain.
            return self._execute_threads_post(start_time)
        elif action_choice == "youtube":
            return self._execute_youtube_upload(start_time)
        elif action_choice == "instagram":
            return self._execute_instagram_carousel(start_time)
        elif action_choice == "devto":
            return self._execute_devto_post(start_time)
        elif action_choice == "pinterest":
            return self._execute_pinterest_pin(start_time)
        elif action_choice == "linkedin-replies":
            return self._execute_linkedin_comment_replies(start_time)
        elif action_choice == "linkedin-peers":
            return self._execute_linkedin_peer_engagement(start_time)
        elif action_choice == "bluesky-replies":
            return self._execute_bluesky_sniper_replies(start_time)
        elif action_choice == "threads-replies":
            return self._execute_threads_sniper_replies(start_time)
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



    def _execute_original_post(self, start_time: float) -> bool:

        """Discovers trending topics and posts a polarizing hot take."""

        console.print("[bold magenta]🚀 Mode: Casual Relatable Post (X)[/bold magenta]")

        # X is a casual profile: focus on everyday human humor, coffee, adulting, remote work quirks.
        trends = self.hunter.get_casual_topics()

        if not trends:
            console.print("[red]No casual topics discovered. Skipping...[/red]")
            self.tracker.record_event(
                action_type="original_post",
                status="skipped",
                skip_or_error_reason="Trend discovery returned 0 items",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        # Select an unused topic
        selected_trend = None
        for t in trends:
            if t["title"] not in self.tracker.history["posted_tweets"]:
                selected_trend = t
                break

        if not selected_trend:
            selected_trend = trends[0]

        console.print(f"[bold]Casual Topic:[/bold] {selected_trend['title']}")

        self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1

        try:
            hot_take = self.ai.generate_casual_x_take(
                selected_trend["title"],
                selected_trend.get("context", selected_trend.get("summary", ""))
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



        # Generate Visual Media: For casual X posts, generate aesthetic dark-mode card & looping GIF for maximum engagement
        twitter_media = None
        try:
            from src.autonomous_visual_engine import generate_casual_visual_card
            casual_png, casual_gif = generate_casual_visual_card(selected_trend["title"], hot_take)
            if casual_gif and Path(casual_gif).exists() and Path(casual_gif).stat().st_size > 0:
                twitter_media = casual_gif
            elif casual_png and Path(casual_png).exists() and Path(casual_png).stat().st_size > 0:
                twitter_media = casual_png
            console.print(f"[bold magenta]🎬 X Visual Media Attachment: {twitter_media}[/bold magenta]")
        except Exception as e:
            console.print(f"[dim]X visual card note: {e}[/dim]")

        # 1. Post to X (Twitter) - Always attach visual card/looping GIF for 10x timeline dwell time
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
        else:
            console.print("[yellow]⚠️ 𝕏 post could not be published. Continuing with remaining platforms...[/yellow]")

        if not success and self.twitter.last_outcome_unknown:
            console.print("[red]X post outcome is unknown; stopping without another X attempt.[/red]")
            return False

        # 2. Cross-post to Bluesky (Technical Take, attaching GIF loop)
        if self.safety.dry_run or (config.BLUESKY_HANDLE and config.BLUESKY_APP_PASSWORD):
            try:
                from src.bluesky_client import BlueskyClient
                bsky_client = BlueskyClient(
                    handle=config.BLUESKY_HANDLE,
                    app_password=config.BLUESKY_APP_PASSWORD,
                    dry_run=self.safety.dry_run
                )
                b_topics = self.hunter.get_linkedin_topics()
                b_trend = b_topics[0] if b_topics else {"title": "Continuous Speculative Decoding", "summary": "Latency analysis on modern open-weights"}
                bsky_take = self.ai.generate_bluesky_take(
                    b_trend["title"],
                    b_trend.get("summary", "")
                )
                bsky_visual = None
                try:
                    from src.autonomous_visual_engine import generate_visual_for_post
                    b_gif, _ = generate_visual_for_post(b_trend["title"], b_trend.get("summary", ""))
                    if b_gif and Path(b_gif).exists() and Path(b_gif).stat().st_size > 0:
                        bsky_visual = b_gif
                except Exception as bve:
                    console.print(f"[dim]Bluesky visual note: {bve}[/dim]")

                bsky_reservation, bsky_reason = self._reserve_platform(
                    "bluesky",
                    "post",
                    f"post:{stable_hash(bsky_take)}",
                    target=b_trend["title"],
                    preview=bsky_take,
                )
                if not self.safety.dry_run and not bsky_reservation:
                    console.print(f"[dim]Bluesky duplicate guard: {bsky_reason}[/dim]")
                    bsky_ok, bsky_msg = False, bsky_reason
                else:
                    bsky_ok, bsky_msg = bsky_client.post(bsky_take, media_path=bsky_visual)
                    self._complete_platform(
                        bsky_reservation,
                        ok=bsky_ok,
                        unknown=getattr(bsky_client, "last_outcome_unknown", False),
                        reason=bsky_msg,
                    )
                if bsky_ok:
                    console.print("[bold cyan]🦋 Also published to Bluesky (@neubench.bsky.social) with animation![/bold cyan]")
                    self.tracker.record_event(
                        action_type="bluesky_post",
                        status="success",
                        target_identifier="Bluesky (@neubench.bsky.social)",
                        content_preview=bsky_take,
                        duration_seconds=1.2,
                        is_dry_run=self.safety.dry_run
                    )
                else:
                    console.print(f"[yellow]Bluesky note: {bsky_msg}[/yellow]")
            except Exception as e:
                console.print(f"[dim]Bluesky dispatch note: {e}[/dim]")

        today_counts = self.tracker.get_today_counts()

        # 4. Cross-post to Threads (Casual Profile)
        try:
            from src.threads_automater import ThreadsAutomater
            th_automater = ThreadsAutomater(headless=True, dry_run=self.safety.dry_run)
            if self.safety.dry_run or th_automater.is_session_available():
                casual_threads_topics = self.hunter.get_casual_topics()
                c_topic = casual_threads_topics[0] if casual_threads_topics else {"title": "The Sunday evening shift", "context": "When the weekend evaporates"}
                th_take = self.ai.generate_casual_threads_take(c_topic["title"], c_topic.get("context", ""))
                th_reservation, th_reason = self._reserve_platform(
                    "threads",
                    "post",
                    f"post:{stable_hash(th_take)}",
                    target=c_topic["title"],
                    preview=th_take,
                )
                if not self.safety.dry_run and not th_reservation:
                    th_ok, th_msg = False, th_reason
                else:
                    th_media = None
                    try:
                        from src.autonomous_visual_engine import generate_casual_visual_card
                        th_png, _ = generate_casual_visual_card(c_topic["title"], th_take, square=True)
                        if th_png and Path(th_png).exists() and Path(th_png).stat().st_size > 0:
                            th_media = th_png
                            console.print(f"[bold magenta]🎬 Threads visual card: {th_media}[/bold magenta]")
                    except Exception as ve:
                        console.print(f"[dim]Threads visual note: {ve}[/dim]")
                    th_ok, th_msg = th_automater.post(th_take, image_path=th_media)
                    self._complete_platform(
                        th_reservation,
                        ok=th_ok,
                        unknown=getattr(th_automater, "last_outcome_unknown", False),
                        reason=th_msg,
                    )
                if th_ok:
                    console.print("[bold magenta]🧵 Also published to Threads (@neubench)![/bold magenta]")
                    try:
                        self.tracker.history.setdefault("posted_tweets", []).append(f"th:{c_topic['title']}")
                        self.tracker.save_history()
                    except Exception:
                        pass
                    self.tracker.record_event(
                        action_type="threads_post",
                        status="success",
                        target_identifier="Threads Community",
                        content_preview=th_take[:80],
                        duration_seconds=15.0,
                        is_dry_run=self.safety.dry_run
                    )
                else:
                    console.print(f"[yellow]Threads note: {th_msg}[/yellow]")
        except Exception as e:
            console.print(f"[dim]Threads dispatch note: {e}[/dim]")

        # Fetch dynamic AI topic for visual/video syndication (deduped across runs)
        used_ai = self.tracker.history.get("posted_ai_topics", [])
        broadcast_topic = self.hunter.get_dynamic_ai_topic(used_topics=used_ai)
        b_title = broadcast_topic.get("title", "AI Systems")
        b_summary = broadcast_topic.get("summary", "")
        b_pro_tip = broadcast_topic.get("pro_tip", "")
        try:
            self.tracker.history.setdefault("posted_ai_topics", []).append(b_title)
            self.tracker.save_history()
        except Exception:
            pass

        # 5. Cross-post to Pinterest Pin (Dynamic Cheatsheet)
        try:
            can_pin, pin_reason = self.safety.can_perform_action("pinterest", today_counts)
            if can_pin:
                from src.pinterest_automater import PinterestAutomater
                from src.instagram_carousel import InstagramCarouselGenerator
                pin_automater = PinterestAutomater(headless=True, dry_run=self.safety.dry_run)
                if self.safety.dry_run or pin_automater.is_session_available():
                    ig_gen = InstagramCarouselGenerator()
                    dynamic_slides = ig_gen.generate_dynamic_carousel(broadcast_topic)
                    cover_img = Path(dynamic_slides[0]) if dynamic_slides else None

                    if cover_img and cover_img.exists():
                        console.print(f"[bold magenta]📌 Publishing Pin to Pinterest: {b_title[:60]}...[/bold magenta]")
                        p_desc = f"{b_title}\n\n{b_summary}\n\n💡 Pro-Tip: {b_pro_tip}\n\nLive AI Benchmarks: https://neubench.netlify.app\n\n#AI #Tech #MachineLearning"
                        pin_reservation, pin_reason = self._reserve_platform(
                            "pinterest",
                            "pin",
                            f"pin:{stable_hash(b_title + chr(10) + p_desc)}",
                            target=b_title,
                            preview=b_title,
                        )
                        if not self.safety.dry_run and not pin_reservation:
                            p_ok, p_msg = False, pin_reason
                        else:
                            p_ok, p_msg = pin_automater.create_pin(
                                image_path=str(cover_img),
                                title=f"{b_title} • AI Cheatsheet"[:80],
                                description=p_desc,
                                link="https://neubench.netlify.app"
                            )
                            self._complete_platform(
                                pin_reservation,
                                ok=p_ok,
                                unknown=getattr(pin_automater, "last_outcome_unknown", False),
                                reason=p_msg,
                            )
                        if p_ok:
                            console.print("[bold green]✅ Pinterest Pin published![/bold green]")
                            self.tracker.record_event(
                                action_type="pinterest_pin",
                                status="success",
                                target_identifier="Pinterest Visual Pin",
                                content_preview=b_title[:80],
                                duration_seconds=15.0,
                                is_dry_run=self.safety.dry_run
                            )
                        else:
                            console.print(f"[yellow]Pinterest note: {p_msg}[/yellow]")
                else:
                    console.print("[yellow]Pinterest skipped: session cookies not found. Run 'python main.py login-pinterest'.[/yellow]")
            else:
                console.print(f"[dim]Pinterest skipped: {pin_reason}[/dim]")
        except Exception as ex:
            console.print(f"[dim]Pinterest broadcast note: {ex}[/dim]")

        # 6. Cross-post to Instagram Carousel (Dynamic 5-Slide Cheatsheet)
        try:
            can_ig, ig_reason = self.safety.can_perform_action("instagram", today_counts)
            if can_ig:
                from src.instagram_carousel import InstagramCarouselGenerator
                from src.instagram_automater import InstagramAutomater
                ig_automater = InstagramAutomater(headless=True, dry_run=self.safety.dry_run)
                if self.safety.dry_run or ig_automater.is_session_available():
                    ig_gen = InstagramCarouselGenerator()
                    slides = ig_gen.generate_dynamic_carousel(broadcast_topic)

                    if slides:
                        console.print(f"[bold magenta]📸 Publishing Dynamic Carousel to Instagram: {b_title}...[/bold magenta]")
                        ig_caption = (
                            f"🧠 {b_title} • Engineering Cheatsheet\n\n"
                            f"⚡ {b_summary}\n\n"
                            "Swipe through the 1-page breakdown ➡️\n\n"
                            f"💡 Pro-Tip: {b_pro_tip}\n\n"
                            "📌 Save for revision!\n"
                            "📊 Live 260+ model benchmarks: neubench.netlify.app\n\n"
                            "#AI #MachineLearning #DeepLearning #AIEngineering #Coding"
                        )
                        ig_reservation, ig_reason = self._reserve_platform(
                            "instagram",
                            "carousel",
                            f"carousel:{stable_hash(b_title + chr(10) + ig_caption)}",
                            target=b_title,
                            preview=ig_caption,
                        )
                        if not self.safety.dry_run and not ig_reservation:
                            ig_ok, ig_msg = False, ig_reason
                        else:
                            ig_ok, ig_msg = ig_automater.post_carousel(slides, ig_caption)
                            self._complete_platform(
                                ig_reservation,
                                ok=ig_ok,
                                unknown=getattr(ig_automater, "last_outcome_unknown", False),
                                reason=ig_msg,
                            )
                        if ig_ok:
                            console.print(f"[bold green]✅ Instagram carousel published![/bold green]")
                            self.tracker.record_event(
                                action_type="instagram_carousel",
                                status="success",
                                target_identifier=f"Instagram Carousel: {b_title}",
                                content_preview=b_title,
                                duration_seconds=20.0,
                                is_dry_run=self.safety.dry_run
                            )
                else:
                    console.print("[yellow]⚠️ Instagram Carousel skipped: session not authenticated. Run 'python main.py login-instagram'.[/yellow]")
            else:
                console.print(f"[dim]Instagram Carousel skipped: {ig_reason}[/dim]")
        except Exception as ex:
            console.print(f"[dim]Instagram broadcast note: {ex}[/dim]")

        # 7. Cross-post to Instagram Reel (Dynamic Video)
        try:
            can_reel, reel_reason = self.safety.can_perform_action("instagram_reel", today_counts)
            if can_reel:
                from src.instagram_automater import InstagramAutomater
                from src.video_generator import VideoGenerator
                ig_automater = InstagramAutomater(headless=True, dry_run=self.safety.dry_run)
                if self.safety.dry_run or ig_automater.is_session_available():
                    vid_gen = VideoGenerator()
                    v_res = vid_gen.generate_dynamic_short(broadcast_topic, dry_run=self.safety.dry_run)
                    reel_video = Path(v_res.get("video_path") or "")

                    reel_caption = (
                        f"⚡ {b_title}\n\n"
                        f"{b_summary}\n\n"
                        f"💡 {b_pro_tip}\n\n"
                        f"📊 Live 260+ model benchmarks: neubench.netlify.app\n\n"
                        "#Reels #AI #MachineLearning #DeepLearning #Coding"
                    )

                    if reel_video.exists():
                        console.print(f"[bold magenta]🎥 Publishing Reel to Instagram (@neubench)...[/bold magenta]")
                        reel_reservation, reel_reason = self._reserve_platform(
                            "instagram",
                            "reel",
                            f"reel:{stable_hash(reel_caption + chr(10) + str(reel_video))}",
                            target=b_title,
                            preview=reel_caption,
                        )
                        if not self.safety.dry_run and not reel_reservation:
                            r_ok, r_msg = False, reel_reason
                        else:
                            r_ok, r_msg = ig_automater.post_reel(str(reel_video), reel_caption)
                            self._complete_platform(
                                reel_reservation,
                                ok=r_ok,
                                unknown=getattr(ig_automater, "last_outcome_unknown", False),
                                reason=r_msg,
                            )
                        if r_ok:
                            console.print(f"[bold green]✅ Instagram Reel published![/bold green]")
                            self.tracker.record_event(
                                action_type="instagram_reel",
                                status="success",
                                target_identifier=f"Instagram Reel: {b_title}",
                                content_preview=b_title,
                                duration_seconds=25.0,
                                is_dry_run=self.safety.dry_run
                            )
                    else:
                        console.print("[yellow]Instagram Reel skipped: dynamic video generation failed.[/yellow]")
                else:
                    console.print("[yellow]⚠️ Instagram Reel skipped: session not authenticated. Run 'python main.py login-instagram'.[/yellow]")
            else:
                console.print(f"[dim]Instagram Reel skipped: {reel_reason}[/dim]")
        except Exception as ex:
            console.print(f"[dim]Instagram Reel broadcast note: {ex}[/dim]")

        # 8. Cross-post to YouTube Shorts (Dynamic Short)
        try:
            can_yt, yt_reason = self.safety.can_perform_action("youtube", today_counts)
            if can_yt:
                from src.youtube_automater import YouTubeAutomater
                from src.video_generator import VideoGenerator
                yt_automater = None if self.safety.dry_run else YouTubeAutomater()
                if self.safety.dry_run:
                    console.print("[yellow][DRY RUN] Would publish the dynamic video to YouTube Shorts.[/yellow]")
                elif yt_automater and yt_automater.is_authenticated:
                    vid_gen = VideoGenerator()
                    v_res = vid_gen.generate_dynamic_short(broadcast_topic, dry_run=self.safety.dry_run)
                    yt_video = Path(v_res.get("video_path") or "")
                    yt_srt = Path(v_res.get("srt_path") or "") if v_res.get("srt_path") else None

                    yt_title = f"{b_title} Explained #Shorts"[:90]
                    yt_desc = (
                        f"⚡ {b_title}: {b_summary}\n\n"
                        f"💡 Pro-Tip: {b_pro_tip}\n\n"
                        f"Live 260+ model benchmarks: https://neubench.netlify.app\n\n"
                        "#Shorts #AI #MachineLearning #DeepLearning #Coding"
                    )

                    if yt_video.exists():
                        console.print(f"[bold magenta]🎬 Uploading Short to YouTube: {yt_title}...[/bold magenta]")
                        yt_reservation, yt_reason = self._reserve_platform(
                            "youtube",
                            "short",
                            f"short:{stable_hash(yt_title + chr(10) + str(yt_video))}",
                            target=b_title,
                            preview=yt_title,
                        )
                        if not self.safety.dry_run and not yt_reservation:
                            y_ok, y_msg = False, yt_reason
                        else:
                            yt_res = yt_automater.upload_short(
                                video_path=str(yt_video),
                                title=yt_title,
                                description=yt_desc,
                                srt_path=str(yt_srt) if yt_srt and yt_srt.exists() else None
                            )
                            y_ok = yt_res is not None
                            self._complete_platform(
                                yt_reservation,
                                ok=y_ok,
                                unknown=getattr(yt_automater, "last_outcome_unknown", False),
                                reason=getattr(yt_automater, "last_message", "YouTube upload error"),
                            )
                        if y_ok:
                            console.print(f"[bold green]✅ YouTube Short live![/bold green]")
                            self.tracker.record_event(
                                action_type="youtube",
                                status="success",
                                target_identifier=f"YouTube Short: {b_title}",
                                content_preview=yt_title,
                                duration_seconds=30.0,
                                is_dry_run=self.safety.dry_run
                            )
                    else:
                        console.print("[yellow]YouTube Short skipped: VideoGenerator could not produce valid video file.[/yellow]")
            else:
                console.print(f"[dim]YouTube Short skipped: {yt_reason}[/dim]")
        except Exception as ex:
            console.print(f"[dim]YouTube broadcast note: {ex}[/dim]")
        
        return success

    def _execute_bluesky_post(self, start_time: float) -> bool:
        """Generates a developer-focused Bluesky take from a trending topic and publishes it."""
        console.print("[bold cyan]🦋 Mode: Bluesky Auto Post (AT Protocol)[/bold cyan]")

        trends = self.hunter.get_linkedin_topics()
        if not trends:
            console.print("[red]No trends discovered. Skipping Bluesky post...[/red]")
            self.tracker.record_event(
                action_type="bluesky_post",
                status="skipped",
                skip_or_error_reason="Trend discovery returned 0 items",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        selected_trend = None
        for t in trends:
            key = f"bsky:{t['title']}"
            if key not in self.tracker.history.get("posted_tweets", []):
                selected_trend = t
                break

        if not selected_trend:
            reason = "All discovered Bluesky topics are already reserved or published."
            console.print(f"[yellow]{reason}[/yellow]")
            self.tracker.record_event(
                action_type="bluesky_post",
                status="skipped",
                target_identifier="Bluesky dedupe",
                skip_or_error_reason=reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return False

        console.print(f"[bold]Trending Topic:[/bold] {selected_trend['title']}")
        self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1

        try:
            bsky_take = self.ai.generate_bluesky_take(
                selected_trend["title"],
                selected_trend.get("summary", "")
            )
        except Exception as e:
            self.tracker.metrics["lifetime_summary"]["ai_generation_failures"] += 1
            console.print(f"[red]AI Generation Error: {e}[/red]")
            self.tracker.record_event(
                action_type="bluesky_post",
                status="failed",
                target_identifier=selected_trend["title"],
                skip_or_error_reason=f"AI generation failed: {e}",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

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

        media_path = None
        try:
            from src.autonomous_visual_engine import generate_visual_for_post

            gif_v, mp4_v = generate_visual_for_post(
                selected_trend["title"],
                selected_trend.get("summary", ""),
            )
            if gif_v and Path(gif_v).exists() and Path(gif_v).stat().st_size > 0:
                media_path = gif_v
            elif mp4_v and Path(mp4_v).exists() and Path(mp4_v).stat().st_size > 0:
                media_path = mp4_v
            if media_path:
                console.print(f"[bold magenta]🎬 Bluesky visual attachment: {media_path}[/bold magenta]")
        except Exception as error:
            console.print(f"[dim]Bluesky visual generation note: {error}[/dim]")

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


    def execute_threads_custom_post(self, text: str) -> bool:
        """Publish dashboard/CLI text through the guarded Threads path."""

        return self._execute_threads_post(time.time(), custom_text=text)


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
                if today_li >= max_li:
                    reason = f"LinkedIn daily cap reached ({today_li}/{max_li})"
                    console.print(f"[yellow]🔔 {reason}. Skipping this slot.[/yellow]")
                    self.tracker.record_event(
                        action_type="linkedin_post",
                        status="skipped",
                        target_identifier="LinkedIn daily cap",
                        skip_or_error_reason=reason,
                        duration_seconds=time.time() - start_time,
                        is_dry_run=False,
                    )
                    return False

                last_post = last_post_at(
                    post_state,
                    self.tracker.metrics.get("recent_events", []),
                )
                if last_post:
                    now_utc = datetime.now(timezone.utc)
                    elapsed_seconds = (now_utc - last_post).total_seconds()
                    minimum_seconds = max(
                        0,
                        config.LINKEDIN_MIN_INTERVAL_MINUTES
                        - config.LINKEDIN_SCHEDULE_GRACE_MINUTES,
                    ) * 60
                    same_slot = cadence_slot_key(last_post) == cadence_slot_key(now_utc)
                    if same_slot or elapsed_seconds < minimum_seconds:
                        if same_slot:
                            slot_start = datetime.fromisoformat(cadence_slot_key(now_utc))
                            remaining_seconds = max(
                                60,
                                (slot_start + timedelta(hours=3) - now_utc).total_seconds(),
                            )
                        else:
                            remaining_seconds = max(60, minimum_seconds - elapsed_seconds)
                        remaining_minutes = max(1, int((remaining_seconds + 59) // 60))
                        reason = f"LinkedIn cadence guard active; next post allowed in about {remaining_minutes} minute(s)"
                        console.print(f"[yellow]⏳ {reason}.[/yellow]")
                        self.tracker.record_event(
                            action_type="linkedin_post",
                            status="skipped",
                            target_identifier="LinkedIn cadence guard",
                            skip_or_error_reason=reason,
                            duration_seconds=time.time() - start_time,
                            is_dry_run=False,
                        )
                        return False

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
                trends = self.hunter.get_linkedin_topics()
                if not trends:
                    console.print("[red]No current AI/tech trends discovered. Skipping LinkedIn post...[/red]")
                    self.tracker.record_event(
                        action_type="linkedin_post",
                        status="skipped",
                        target_identifier="LinkedIn trends",
                        skip_or_error_reason="Trend discovery returned 0 current AI/tech items",
                        duration_seconds=time.time() - start_time,
                        is_dry_run=self.safety.dry_run,
                    )
                    return False

                selected_trend = {}
                for trend in trends:
                    title = str(trend.get("title", "")).strip()
                    if not title or post_is_duplicate(
                        post_state,
                        title=title,
                        url=trend.get("url", ""),
                    ):
                        continue
                    console.print(f"[bold]LinkedIn Topic:[/bold] {title}")
                    self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1
                    try:
                        candidate_text = self.ai.generate_linkedin_take(
                            title,
                            trend.get("summary", ""),
                            company=trend.get("company", "NeuBench"),
                        )
                    except Exception as error:
                        self.tracker.metrics["lifetime_summary"]["ai_generation_failures"] += 1
                        console.print(f"[red]AI Generation Error: {error}[/red]")
                        self.tracker.record_event(
                            action_type="linkedin_post",
                            status="failed",
                            target_identifier=title,
                            skip_or_error_reason=f"AI generation failed: {error}",
                            duration_seconds=time.time() - start_time,
                            is_dry_run=self.safety.dry_run,
                        )
                        return False
                    if post_is_duplicate(post_state, title=title, url=trend.get("url", ""), content=candidate_text):
                        console.print("[dim]Generated body matched recent LinkedIn content; trying another topic.[/dim]")
                        continue
                    selected_trend = trend
                    li_text = candidate_text
                    break

                if not selected_trend:
                    reason = "All discovered LinkedIn topics or generated bodies were already posted recently"
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

            console.print(f"[green]Generated LinkedIn Draft:[/green] {li_text[:120]}...")
            media_path = None
            try:
                from src.autonomous_visual_engine import generate_visual_for_post

                gif_v, mp4_v = generate_visual_for_post(
                    selected_trend["title"],
                    selected_trend.get("summary", ""),
                )
                if mp4_v and Path(mp4_v).exists() and Path(mp4_v).stat().st_size > 0:
                    media_path = mp4_v
                elif gif_v and Path(gif_v).exists() and Path(gif_v).stat().st_size > 0:
                    media_path = gif_v
                console.print(f"[bold magenta]🎬 LinkedIn visual attachment: {media_path}[/bold magenta]")
            except Exception as error:
                console.print(f"[dim]LinkedIn visual generation note: {error}[/dim]")

            first_comm = None
            try:
                first_comm = self.ai.generate_first_comment_value_drop(selected_trend["title"], li_text)
                if first_comm:
                    console.print(f"[bold cyan]💬 LinkedIn First Comment Ready (Zero-Link Body):[/bold cyan] {first_comm[:100]}...")
            except Exception as error:
                console.print(f"[dim]First-comment generation note: {error}[/dim]")

            ok, msg = automater.post(li_text, image_path=media_path, first_comment=first_comm)
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




    def _execute_threads_post(self, start_time: float, custom_text: Optional[str] = None) -> bool:
        """Generates a casual Threads post and publishes it via saved session."""
        console.print("[bold magenta]Mode: Threads Auto Post (Community)[/bold magenta]")

        can_threads, threads_reason = self.safety.can_perform_action(
            "threads", self.tracker.get_today_counts()
        )
        if not can_threads:
            console.print(f"[yellow]Threads skipped: {threads_reason}[/yellow]")
            return False

        from src.threads_automater import ThreadsAutomater
        automater = ThreadsAutomater(headless=True, dry_run=self.safety.dry_run)

        trends = self.hunter.get_casual_topics() if custom_text is None else []
        pool = trends or []
        if custom_text is not None:
            selected_trend = {
                "title": "Custom Threads post",
                "summary": "",
            }
        elif not pool:
            selected_trend = {
                "title": "Second iced coffee at 4 PM",
                "summary": "Drinking cold brew late in the afternoon and acting shocked when you can't sleep at 2 AM.",
            }
        else:
            selected_trend = None
            for t in pool:
                key = f"th:{t['title']}"
                if key not in self.tracker.history.get("posted_tweets", []):
                    selected_trend = t
                    break
            if not selected_trend:
                selected_trend = pool[0]

        console.print(f"[bold]Casual Topic:[/bold] {selected_trend['title']}")
        if custom_text is not None:
            th_text = str(custom_text).strip()
            if not th_text:
                self.tracker.record_event(
                    action_type="threads_post",
                    status="skipped",
                    target_identifier="Threads input",
                    skip_or_error_reason="Custom Threads text is empty.",
                    duration_seconds=time.time() - start_time,
                    is_dry_run=self.safety.dry_run,
                )
                return False
        else:
            self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1
            try:
                th_text = self.ai.generate_casual_threads_take(
                    selected_trend["title"],
                    selected_trend.get("context", selected_trend.get("summary", ""))
                )
            except Exception as e:
                self.tracker.metrics["lifetime_summary"]["ai_generation_failures"] += 1
                console.print(f"[red]AI Generation Error: {e}[/red]")
                self.tracker.record_event(
                    action_type="threads_post",
                    status="failed",
                    target_identifier=selected_trend["title"],
                    skip_or_error_reason=f"AI generation failed: {e}",
                    duration_seconds=time.time() - start_time,
                    is_dry_run=self.safety.dry_run
                )
                return False

        console.print(f"[green]Generated Threads Draft:[/green] {th_text[:120]}...")

        if not self.safety.dry_run and not automater.is_session_available():
            console.print("[yellow]Threads session not available. Run 'python main.py login-threads'. Skipping.[/yellow]")
            self.tracker.record_event(
                action_type="threads_post",
                status="skipped",
                target_identifier=selected_trend["title"],
                content_preview=th_text,
                skip_or_error_reason="Threads session not authenticated",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        identity = f"post:{stable_hash(th_text)}"
        reservation_id, reservation_reason = self._reserve_platform(
            "threads",
            "post",
            identity,
            target=selected_trend["title"],
            preview=th_text,
        )
        if not self.safety.dry_run and not reservation_id:
            self.tracker.record_event(
                action_type="threads_post",
                status="skipped",
                target_identifier=selected_trend["title"],
                content_preview=th_text,
                skip_or_error_reason=reservation_reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=False,
            )
            return False

        th_media = None
        try:
            from src.autonomous_visual_engine import generate_casual_visual_card
            casual_png, _ = generate_casual_visual_card(selected_trend["title"], th_text, square=True)
            if casual_png and Path(casual_png).exists() and Path(casual_png).stat().st_size > 0:
                th_media = casual_png
                console.print(f"[bold magenta]🎬 Threads visual card attachment: {th_media}[/bold magenta]")
        except Exception as ve:
            console.print(f"[dim]Threads visual note: {ve}[/dim]")

        try:
            ok, msg = automater.post(th_text, image_path=th_media)
        except Exception as error:
            ok, msg = False, f"Threads client error: {error}"
        self._complete_platform(
            reservation_id,
            ok=ok,
            unknown=getattr(automater, "last_outcome_unknown", False),
            reason=msg,
        )
        status = "success" if ok else "failed"
        self.tracker.record_event(
            action_type="threads_post",
            status=status,
            target_identifier="Threads Community",
            content_preview=th_text,
            skip_or_error_reason="" if ok else msg,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )

        if ok:
            console.print(f"[bold magenta]OK {msg}[/bold magenta]")
            try:
                self.tracker.history.setdefault("posted_tweets", []).append(f"th:{selected_trend['title']}")
                self.tracker.save_history()
            except Exception:
                pass
        else:
            console.print(f"[red]Threads publish failed: {msg}[/red]")

        return ok



    def _resolve_algorithmic_action(self, today_counts: Dict[str, int]) -> str:
        """
        Resolves action based on the 5 Algorithmic Peak Windows and anti-cannibalization limits.
        """
        current_hour_utc = datetime.now(timezone.utc).hour
        
        # Check active window
        for win_id, win in config.ALGORITHMIC_WINDOWS.items():
            if win["utc_start"] <= current_hour_utc < win["utc_end"]:
                console.print(f"\n[bold cyan]⏰ Active Algorithmic Window: {win['name']} ({win['ist_display']} / {win['est_display']})[/bold cyan]")
                for action in win["primary_actions"]:
                    action_key = "youtube" if action == "youtube_reel" else action
                    can_do, _ = self.safety.can_perform_action(action_key, today_counts)
                    if can_do:
                        console.print(f"[bold green]🎯 Algorithmic Selection: '{action_key}' for {win['name']}[/bold green]")
                        return action_key

        # Outside peak windows: Opportunity-Driven Viral Engagement across X, Threads, Bluesky & LinkedIn
        console.print("[dim]Outside peak broadcast windows: Scanning for active viral discussions across X, Threads, Bluesky & LinkedIn...[/dim]")
        
        reply_candidates = []
        can_reply, _ = self.safety.can_perform_action("reply", today_counts)
        if can_reply:
            reply_candidates.append("reply")

        can_bs_reply, _ = self.safety.can_perform_action("bluesky-replies", today_counts)
        if can_bs_reply and self.bluesky.is_configured():
            reply_candidates.append("bluesky-replies")

        can_th_reply, _ = self.safety.can_perform_action("threads-replies", today_counts)
        if can_th_reply:
            reply_candidates.append("threads-replies")

        if reply_candidates:
            # Randomize or pick least executed to evenly distribute high-signal replies
            selected_reply = random.choice(reply_candidates)
            console.print(f"[bold magenta]💬 Multi-Platform Sniper Reply Selected: '{selected_reply}'[/bold magenta]")
            return selected_reply

        can_post, _ = self.safety.can_perform_action("post", today_counts)
        if can_post:
            return "post"

        return "repost"

    def _execute_youtube_upload(self, start_time: float) -> bool:
        """Publishes an on-demand, dynamic AI topic Short with voiceover and dual subtitles."""
        console.print("[bold magenta]🎬 Mode: YouTube Shorts Dynamic Publishing[/bold magenta]")
        from src.youtube_automater import YouTubeAutomater
        from src.video_generator import VideoGenerator

        used_ai = self.tracker.history.get("posted_ai_topics", [])
        topic_data = self.hunter.get_dynamic_ai_topic(used_topics=used_ai)
        topic_title = topic_data.get("title", "AI Concept")
        title = f"{topic_title} Explained #Shorts"[:90]
        desc = (
            f"⚡ {topic_title}: {topic_data.get('summary', '')}\n\n"
            f"💡 Engineering Rule: {topic_data.get('pro_tip', '')}\n\n"
            "📊 Live 260+ model benchmarks: https://neubench.netlify.app\n\n"
            "#Shorts #AI #MachineLearning #DeepLearning #Python #SoftwareEngineering #DataScience"
        )

        yt = YouTubeAutomater()
        if self.safety.dry_run:
            console.print(f"[bold yellow][DRY RUN] Would generate & upload YouTube Short: {title}[/bold yellow]")
            self.tracker.record_event(
                action_type="youtube",
                status="dry_run",
                target_identifier=topic_title,
                content_preview=title,
                duration_seconds=time.time() - start_time,
                is_dry_run=True,
            )
            return True

        if not yt.is_authenticated:
            console.print("[yellow]YouTube service not authenticated. Run 'python main.py login-youtube'. Skipping.[/yellow]")
            self.tracker.record_event(
                action_type="youtube",
                status="skipped",
                target_identifier=topic_title,
                skip_or_error_reason="YouTube credentials not authenticated",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        # Dynamically generate vertical short
        vid_gen = VideoGenerator()
        res_paths = vid_gen.generate_dynamic_short(topic_data, dry_run=self.safety.dry_run)
        yt_video = Path(res_paths.get("video_path") or "")
        yt_srt = Path(res_paths.get("srt_path") or "") if res_paths.get("srt_path") else None

        if not yt_video.exists():
            console.print("[cyan]Video generation failed; generating dynamic visual MP4...[/cyan]")
            try:
                from src.autonomous_visual_engine import generate_visual_for_post
                _gif, generated_mp4 = generate_visual_for_post(topic_title, topic_data.get("summary", ""))
                if generated_mp4 and Path(generated_mp4).exists():
                    yt_video = Path(generated_mp4)
                    yt_srt = None
            except Exception as error:
                console.print(f"[dim]YouTube visual generation note: {error}[/dim]")

        if not yt_video.exists():
            reason = "Failed to render video asset for YouTube Short."
            self.tracker.record_event(
                action_type="youtube",
                status="skipped",
                target_identifier=topic_title,
                skip_or_error_reason=reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=False,
            )
            return False

        identity = f"short:{stable_hash(title + chr(10) + str(yt_video))}"
        reservation_id, reservation_reason = self._reserve_platform(
            "youtube", "short", identity, target=title, preview=title
        )
        if not reservation_id:
            self.tracker.record_event(
                action_type="youtube",
                status="skipped",
                target_identifier=topic_title,
                content_preview=title,
                skip_or_error_reason=reservation_reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=False,
            )
            return False

        try:
            res = yt.upload_short(video_path=str(yt_video), title=title, description=desc, srt_path=str(yt_srt) if yt_srt and yt_srt.exists() else None)
        except Exception as error:
            res = None
            yt.last_outcome_unknown = True
            yt.last_message = f"YouTube client error: {error}"
        ok = res is not None
        self._complete_platform(
            reservation_id,
            ok=ok,
            unknown=getattr(yt, "last_outcome_unknown", False),
            reason=getattr(yt, "last_message", "YouTube upload failed"),
        )
        status = "success" if ok else "failed"
        url = res.get("url", "") if res else ""
        
        self.tracker.record_event(
            action_type="youtube",
            status=status,
            target_identifier=topic_title,
            content_preview=title,
            skip_or_error_reason="" if ok else getattr(yt, "last_message", "YouTube API upload error"),
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )
        if ok:
            console.print(f"[bold green]✅ YouTube Short live: {url}[/bold green]")
            # Syndicate to Pinterest video pin
            try:
                from src.pinterest_automater import PinterestAutomater
                pin_auto = PinterestAutomater(headless=True, dry_run=self.safety.dry_run)
                if pin_auto.is_session_available():
                    console.print("[bold cyan]Syndicating video to Pinterest...[/bold cyan]")
                    pin_auto.create_pin(
                        image_path=str(yt_video),
                        title=title[:80],
                        description=desc,
                        link="https://neubench.netlify.app"
                    )
            except Exception as e:
                console.print(f"[dim]Pinterest video syndication notice: {e}[/dim]")

        return ok

    def _execute_instagram_carousel(self, start_time: float) -> bool:
        """Renders and publishes a dynamic 5-slide technical carousel to Instagram."""
        console.print("[bold magenta]📸 Mode: Instagram Dynamic Carousel Publishing[/bold magenta]")
        from src.instagram_carousel import InstagramCarouselGenerator
        from src.instagram_automater import InstagramAutomater

        used_ai = self.tracker.history.get("posted_ai_topics", [])
        topic_data = self.hunter.get_dynamic_ai_topic(used_topics=used_ai)
        topic_title = topic_data.get("title", "AI Concept")

        automater = InstagramAutomater(headless=True, dry_run=self.safety.dry_run)
        if not self.safety.dry_run and not automater.is_session_available():
            console.print("[yellow]Instagram session not available. Run 'python main.py login-instagram'. Skipping.[/yellow]")
            self.tracker.record_event(
                action_type="instagram",
                status="skipped",
                target_identifier=topic_title,
                skip_or_error_reason="Instagram session not authenticated",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        gen = InstagramCarouselGenerator()
        slides = gen.generate_dynamic_carousel(topic_data)
        if not slides:
            reason = "Failed to render dynamic carousel slides."
            self.tracker.record_event(
                action_type="instagram",
                status="skipped",
                target_identifier=topic_title,
                skip_or_error_reason=reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run,
            )
            return False

        caption = (
            f"🧠 {topic_title} • Engineering Cheatsheet\n\n"
            f"⚡ {topic_data.get('summary', '')}\n\n"
            "Swipe through the 1-page breakdown ➡️\n\n"
            f"💡 Pro-Tip: {topic_data.get('pro_tip', '')}\n\n"
            "📌 Save this post for your revision!\n"
            "📊 Live 260+ model benchmarks: neubench.netlify.app\n\n"
            "#AI #MachineLearning #AIEngineering #Coding #Developers #Tech"
        )
        identity = f"carousel:{stable_hash(topic_title + chr(10) + caption)}"
        reservation_id, reservation_reason = self._reserve_platform(
            "instagram", "carousel", identity, target=topic_title, preview=caption
        )
        if not self.safety.dry_run and not reservation_id:
            self.tracker.record_event(
                action_type="instagram",
                status="skipped",
                target_identifier=topic_title,
                content_preview=caption[:100],
                skip_or_error_reason=reservation_reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=False,
            )
            return False
        try:
            ok, msg = automater.post_carousel(slides, caption)
        except Exception as error:
            ok, msg = False, f"Instagram client error: {error}"
        self._complete_platform(
            reservation_id,
            ok=ok,
            unknown=getattr(automater, "last_outcome_unknown", False),
            reason=msg,
        )
        status = "success" if ok else "failed"
        self.tracker.record_event(
            action_type="instagram",
            status=status,
            target_identifier=topic_title,
            content_preview=caption[:100],
            skip_or_error_reason="" if ok else msg,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )
        if ok:
            console.print(f"[bold green]✅ Instagram Carousel published![/bold green]")
        return ok

    def _execute_devto_post(self, start_time: float) -> bool:
        """Publishes a comprehensive deep-dive AI article dynamically to Dev.to."""
        console.print("[bold magenta]📝 Mode: Dev.to Deep-Dive Article Publishing[/bold magenta]")
        from src.devto_automater import DevToAutomater

        used_ai = self.tracker.history.get("posted_ai_topics", [])
        topic_data = self.hunter.get_dynamic_ai_topic(used_topics=used_ai)
        topic_title = topic_data.get("title", "AI Architecture")
        title = f"{topic_title}: Deep Dive & Engineering Breakdown"

        devto = DevToAutomater()
        if self.safety.dry_run:
            self.tracker.record_event(
                action_type="devto",
                status="dry_run",
                target_identifier=topic_title,
                content_preview=title,
                duration_seconds=time.time() - start_time,
                is_dry_run=True,
            )
            return True

        if not devto.is_configured():
            console.print("[yellow]Dev.to API key not configured. Skipping.[/yellow]")
            return False

        try:
            lesson_body = self.ai.generate_dynamic_technical_article(topic_data)
        except Exception as error:
            self.tracker.record_event(
                action_type="devto",
                status="failed",
                target_identifier=topic_title,
                skip_or_error_reason=f"Dev.to article generation failed: {error}",
                duration_seconds=time.time() - start_time,
                is_dry_run=False,
            )
            return False

        identity = f"article:{stable_hash(title + chr(10) + lesson_body)}"
        reservation_id, reservation_reason = self._reserve_platform(
            "devto", "article", identity, target=title, preview=title
        )
        if not reservation_id:
            self.tracker.record_event(
                action_type="devto",
                status="skipped",
                target_identifier=title,
                content_preview=title,
                skip_or_error_reason=reservation_reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=False,
            )
            return False
        try:
            ok, msg, url = devto.create_article(title=title, body_markdown=lesson_body, series="AI Engineering & Architectures")
        except Exception as error:
            ok, msg, url = False, f"Dev.to client error: {error}", None
        self._complete_platform(
            reservation_id,
            ok=ok,
            unknown=getattr(devto, "last_outcome_unknown", False),
            reason=msg,
        )
        status = "success" if ok else "failed"
        self.tracker.record_event(
            action_type="devto",
            status=status,
            target_identifier=title,
            content_preview=title,
            skip_or_error_reason="" if ok else msg,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )
        if ok:
            console.print(f"[bold green]✅ Dev.to article live: {url}[/bold green]")
        return ok

    def _execute_pinterest_pin(self, start_time: float) -> bool:
        """Publishes an infographic pin to Pinterest dynamically."""
        console.print("[bold magenta]📌 Mode: Pinterest Infographic Pin Publishing[/bold magenta]")
        from src.pinterest_automater import PinterestAutomater
        from src.instagram_carousel import InstagramCarouselGenerator

        used_ai = self.tracker.history.get("posted_ai_topics", [])
        topic_data = self.hunter.get_dynamic_ai_topic(used_topics=used_ai)
        topic_title = topic_data.get("title", "AI Architecture")

        pin_automater = PinterestAutomater(headless=True, dry_run=self.safety.dry_run)
        if not self.safety.dry_run and not pin_automater.is_session_available():
            console.print("[yellow]Pinterest session not available. Skipping.[/yellow]")
            return False

        gen = InstagramCarouselGenerator()
        slides = gen.generate_dynamic_carousel(topic_data)
        if not slides and not self.safety.dry_run:
            reason = "Failed to render dynamic visual cover for Pinterest."
            self.tracker.record_event(
                action_type="pinterest",
                status="skipped",
                target_identifier=topic_title,
                skip_or_error_reason=reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=False,
            )
            return False

        cover_img = slides[0] if slides else ""
        pin_title = f"{topic_title} • AI Cheatsheet"[:80]
        pin_desc = f"{topic_title}: {topic_data.get('summary', '')} 💡 Pro-Tip: {topic_data.get('pro_tip', '')}. Save for revision! Live benchmarks at https://neubench.netlify.app"
        
        identity = f"pin:{stable_hash(pin_title + chr(10) + pin_desc)}"
        reservation_id, reservation_reason = self._reserve_platform(
            "pinterest", "pin", identity, target=pin_title, preview=pin_title
        )
        if not self.safety.dry_run and not reservation_id:
            self.tracker.record_event(
                action_type="pinterest",
                status="skipped",
                target_identifier=pin_title,
                content_preview=pin_title,
                skip_or_error_reason=reservation_reason,
                duration_seconds=time.time() - start_time,
                is_dry_run=False,
            )
            return False
        try:
            ok, msg = pin_automater.create_pin(cover_img, pin_title, pin_desc, link="https://neubench.netlify.app")
        except Exception as error:
            ok, msg = False, f"Pinterest client error: {error}"
        self._complete_platform(
            reservation_id,
            ok=ok,
            unknown=getattr(pin_automater, "last_outcome_unknown", False),
            reason=msg,
        )
        status = "success" if ok else "failed"
        self.tracker.record_event(
            action_type="pinterest",
            status=status,
            target_identifier=pin_title,
            content_preview=pin_title,
            skip_or_error_reason="" if ok else msg,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )
        if ok:
            console.print(f"[bold green]✅ Pinterest Pin live![/bold green]")
        return ok

    def start_scheduler(self):

        """Runs the continuous loop with randomized intervals to avoid bot detection."""

        console.print("\n" + "="*60, style="bold cyan")

        console.print("🤖 X-Post-Automater Active & Running (Daemon Mode)", style="bold green")

        console.print(f"Daily Cap: {self.safety.max_daily_total} total actions/day (Dry Run: {self.safety.dry_run})", style="yellow")

        console.print("="*60 + "\n", style="bold cyan")



        while True:

            try:

                self.run_single_cycle()

            except Exception as e:

                console.print(f"[bold red]Cycle Error: {e}[/bold red]")



            sleep_minutes = random.randint(

                config.POST_INTERVAL_MIN_MINUTES,

                config.POST_INTERVAL_MAX_MINUTES

            )

            console.print(f"\n[dim]💤 Sleeping for {sleep_minutes} minutes before next post...[/dim]\n")

            time.sleep(sleep_minutes * 60)


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

    def _execute_threads_sniper_replies(self, start_time: float) -> bool:
        """Finds trending viral discussions across tech, work-life, and culture on Threads and replies."""
        console.print("[bold magenta]🧵 Mode: Threads Viral Discussion Sniper Replies[/bold magenta]")
        from src.threads_automater import ThreadsAutomater
        th = ThreadsAutomater(headless=True, dry_run=self.safety.dry_run)
        if not th.is_session_available():
            console.print("[yellow]Threads session not available for replying. Skipping.[/yellow]")
            return False
        queries = ["AI tech", "software engineer", "startup life", "remote work", "coding tips"]
        q = random.choice(queries)
        count, msg = th.reply_to_viral_threads(query=q, max_replies=1)
        self.tracker.record_event(
            action_type="threads_reply",
            status="success" if count > 0 else "skipped",
            target_identifier=f"Threads Viral ({q})",
            content_preview=msg,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )
        return count > 0
