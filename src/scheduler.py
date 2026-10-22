import sys
import time
import json
import random
from datetime import datetime, timezone
from pathlib import Path

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

console = Console()

# Target high-engagement accounts for explosive reach (Indian + Global tech giants)
VIRAL_ACCOUNTS = [
    # Top Indian Reach & National / Tech Accounts
    "narendramodi",
    "IndianTechGuide",
    "peakbengaluru",
    "ANI",
    "NDTV",
    "thetanmay",
    "kunalb11",
    "Zomato",
    # Global Tech & AI Heavyweights
    "elonmusk",
    "sama",
    "karpathy",
    "satyanadella",
    "ylecun",
    "levelsio",
    "PopBase",
    "WatcherGuru",
    "unusual_whales"
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
        if force_action in ("post", "reply", "repost", "bluesky"):
            action_choice = force_action
        else:
            # Distribution: 60% Reply, 20% Repost (Quote-Tweet), 20% Original Post
            roll = random.randint(1, 100)
            if roll <= 60:
                action_choice = "reply"
            elif roll <= 80:
                action_choice = "repost"
            else:
                action_choice = "post"

        # 4. Enforce quota check
        can_proceed, reason = self.safety.can_perform_action(action_choice, today_counts)
        if not can_proceed:
            console.print(f"[yellow]⚠️ Action '{action_choice}' blocked: {reason}[/yellow]")
            # Attempt fallback to alternative action if total limit is not exceeded
            if today_counts.get("total_actions", 0) < self.safety.max_daily_total:
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
            return self._execute_sniper_reply(start_time)
        elif action_choice == "repost":
            return self._execute_quote_tweet(start_time)
        elif action_choice == "bluesky":
            return self._execute_bluesky_post(start_time)
        else:
            return self._execute_original_post(start_time)

    def _execute_sniper_reply(self, start_time: float) -> bool:
        """Finds a viral account, extracts latest tweet, and replies with high-engagement AI take."""
        console.print("[bold yellow]🎯 Mode: Sniper Reply on Viral Account[/bold yellow]")
        
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

        # Post reply
        success = self.twitter.post_reply(tweet_url, reply_content)
        status = "success" if success else "failed"
        self.tracker.record_event(
            action_type="reply",
            status=status,
            target_identifier=tweet_url,
            content_preview=reply_content,
            skip_or_error_reason="" if success else "Playwright selector or network failure",
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )
        if success:
            console.print("[bold green]✅ Successfully sniped reply![/bold green]")
        return success

    def _execute_quote_tweet(self, start_time: float) -> bool:
        """Finds a viral tweet and Quote-Tweets it with commentary ('masala on top')."""
        console.print("[bold blue]🔁 Mode: Quote-Tweet ('Repost with Masala')[/bold blue]")
        
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

        success = self.twitter.post_quote_tweet(tweet_url, commentary)
        status = "success" if success else "failed"
        self.tracker.record_event(
            action_type="quote_tweet",
            status=status,
            target_identifier=tweet_url,
            content_preview=commentary,
            skip_or_error_reason="" if success else "Playwright quote-tweet failure",
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )
        if success:
            console.print("[bold green]✅ Successfully published quote tweet![/bold green]")
        return success

    def _execute_original_post(self, start_time: float) -> bool:
        """Discovers trending topics and posts a polarizing hot take."""
        console.print("[bold magenta]🚀 Mode: Original Debate Hot Take[/bold magenta]")

        trends = self.hunter.get_curated_trending_topics()
        if not trends:
            console.print("[red]No trends discovered. Skipping...[/red]")
            self.tracker.record_event(
                action_type="original_post",
                status="skipped",
                skip_or_error_reason="Trend discovery returned 0 items",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        # Select an unused trend
        selected_trend = None
        for t in trends:
            if t["title"] not in self.tracker.history["posted_tweets"]:
                selected_trend = t
                break

        if not selected_trend and trends:
            # Re-engage with a fresh take on the top trending item
            selected_trend = random.choice(trends)
            console.print(f"[dim]Re-analyzing top trending topic with fresh angle: {selected_trend['title']}[/dim]")
        elif not selected_trend:
            selected_trend = {
                "title": "Frontier AI Benchmark Discrepancies",
                "summary": "Tracking model performance drift and benchmark evaluations across LLMs on NeuBench."
            }

        console.print(f"[bold]Trending Topic:[/bold] {selected_trend['title']}")
        self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1
        try:
            hot_take = self.ai.generate_hot_take(
                selected_trend["title"],
                selected_trend.get("summary", "")
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

        success = self.twitter.post_tweet(hot_take)
        status = "success" if success else "failed"
        self.tracker.record_event(
            action_type="original_post",
            status=status,
            target_identifier=selected_trend["title"],
            content_preview=hot_take,
            skip_or_error_reason="" if success else "Playwright compose failure",
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )
        if success:
            console.print("[bold green]✅ Successfully published tweet on 𝕏![/bold green]")
            # Cross-post to Bluesky if configured
            if config.BLUESKY_HANDLE and config.BLUESKY_APP_PASSWORD:
                try:
                    from src.bluesky_client import BlueskyClient
                    bsky_client = BlueskyClient(
                        handle=config.BLUESKY_HANDLE,
                        app_password=config.BLUESKY_APP_PASSWORD,
                        dry_run=self.safety.dry_run
                    )
                    bsky_take = self.ai.generate_bluesky_take(
                        selected_trend["title"],
                        selected_trend.get("summary", "")
                    )
                    bsky_ok, bsky_msg = bsky_client.post(bsky_take)
                    if bsky_ok:
                        console.print("[bold cyan]🦋 Also published to Bluesky (@neubench.bsky.social)![/bold cyan]")
                        self.tracker.record_event(
                            action_type="bluesky_post",
                            status="success",
                            target_identifier="Bluesky (@neubench.bsky.social)",
                            content_preview=bsky_take,
                            duration_seconds=1.2,
                            is_dry_run=self.safety.dry_run
                        )
                except Exception as e:
                    console.print(f"[dim]Bluesky dispatch note: {e}[/dim]")

        return success

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
