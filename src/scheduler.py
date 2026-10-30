import sys

import time

import json

import random

from datetime import datetime, timezone

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



console = Console()



# Target high-engagement accounts for explosive reach (Indian + Global tech giants)

VIRAL_ACCOUNTS = [
    # Mega-reach Indian National & Tech Accounts (Highest impression velocity & Modi replies)
    "narendramodi",       # Highest view velocity
    "AshwiniVaishnaw",    # Union Minister for IT & Electronics / IndiaAI
    "IndianTechGuide",
    "peakbengaluru",
    "ANI",
    "NDTV",
    "thetanmay",
    "kunalb11",
    "Zomato",
    "swiggy",
    # Global Tech & AI Heavyweights
    "elonmusk",
    "sama",
    "satyanadella",
    "sundarpichai",
    "karpathy",
    "ylecun",
    "mkbhd",
    "levelsio",
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
        valid_forces = ("post", "reply", "repost", "bluesky", "linkedin", "threads", "omnichannel", "post-all", "youtube", "instagram", "devto", "pinterest")
        if force_action in valid_forces:
            action_choice = force_action
        else:
            action_choice = self._resolve_algorithmic_action(today_counts)

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
            ok = self._execute_sniper_reply(start_time)
            if not ok:
                console.print("[yellow]Reply mode skipped/failed. Falling back to Omnichannel broadcast...[/yellow]")
                return self._execute_original_post(start_time)
            return ok
        elif action_choice == "repost":
            ok = self._execute_quote_tweet(start_time)
            if not ok:
                console.print("[yellow]Quote tweet mode skipped/failed. Falling back to Omnichannel broadcast...[/yellow]")
                return self._execute_original_post(start_time)
            return ok
        elif action_choice == "bluesky":
            return self._execute_bluesky_post(start_time)
        elif action_choice == "linkedin":
            ok = self._execute_linkedin_post(start_time)
            if not ok:
                console.print("[yellow]LinkedIn mode skipped/failed. Falling back to Omnichannel broadcast...[/yellow]")
                return self._execute_original_post(start_time)
            return ok
        elif action_choice == "threads":
            ok = self._execute_threads_post(start_time)
            if not ok:
                console.print("[yellow]Threads mode skipped/failed. Falling back to Omnichannel broadcast...[/yellow]")
                return self._execute_original_post(start_time)
            return ok
        elif action_choice == "youtube":
            return self._execute_youtube_upload(start_time)
        elif action_choice == "instagram":
            return self._execute_instagram_carousel(start_time)
        elif action_choice == "devto":
            return self._execute_devto_post(start_time)
        elif action_choice == "pinterest":
            return self._execute_pinterest_pin(start_time)
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
        else:
            console.print("[yellow]⚠️ 𝕏 post could not be published. Continuing with remaining platforms...[/yellow]")

        # 2. Cross-post to Bluesky (Independent)
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
                else:
                    console.print(f"[yellow]Bluesky note: {bsky_msg}[/yellow]")
            except Exception as e:
                console.print(f"[dim]Bluesky dispatch note: {e}[/dim]")

        # 3. Cross-post to LinkedIn (Independent)
        try:
            from src.linkedin_automater import LinkedInAutomater
            li_automater = LinkedInAutomater(headless=True, dry_run=self.safety.dry_run)
            if li_automater.is_session_available():
                li_take = self.ai.generate_linkedin_take(
                    selected_trend["title"],
                    selected_trend.get("summary", ""),
                    company=selected_trend.get("company", "NeuBench")
                )
                li_ok, li_msg = li_automater.post(li_take)
                if li_ok:
                    console.print("[bold blue]💼 Also published to LinkedIn![/bold blue]")
                    self.tracker.record_event(
                        action_type="linkedin_post",
                        status="success",
                        target_identifier="LinkedIn B2B",
                        content_preview=li_take[:80],
                        duration_seconds=15.0,
                        is_dry_run=self.safety.dry_run
                    )
                else:
                    console.print(f"[yellow]LinkedIn note: {li_msg}[/yellow]")
        except Exception as e:
            console.print(f"[dim]LinkedIn dispatch note: {e}[/dim]")

        # 4. Cross-post to Threads (Independent)
        try:
            from src.threads_automater import ThreadsAutomater
            th_automater = ThreadsAutomater(headless=True, dry_run=self.safety.dry_run)
            if th_automater.is_session_available():
                th_take = self.ai.generate_threads_take(
                    selected_trend["title"],
                    selected_trend.get("summary", ""),
                    company=selected_trend.get("company", "NeuBench")
                )
                th_ok, th_msg = th_automater.post(th_take)
                if th_ok:
                    console.print("[bold magenta]🧵 Also published to Threads (@neubench)![/bold magenta]")
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

        return success

    def _execute_bluesky_post(self, start_time: float) -> bool:
        """Generates a developer-focused Bluesky take from a trending topic and publishes it."""
        console.print("[bold cyan]🦋 Mode: Bluesky Auto Post (AT Protocol)[/bold cyan]")

        trends = self.hunter.get_curated_trending_topics()
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

        if not selected_trend and trends:
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

        if not self.bluesky.is_configured():
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

        ok, msg = self.bluesky.post(bsky_take)
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


    def _execute_linkedin_post(self, start_time: float) -> bool:
        """Publishes the next progressive lesson of the 90-day 'AI Explained: Zero to Advanced' master curriculum."""
        console.print("[bold blue]🎓 Mode: LinkedIn AI Explained Master Series (Day-by-Day)[/bold blue]")

        # Daily cap: max 2 LinkedIn posts/day
        today_li = sum(
            1 for e in self.tracker.metrics.get("recent_events", [])
            if e.get("timestamp", "").startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            and e.get("status") == "success" and not e.get("is_dry_run", False) and e.get("action_type") == "linkedin_post"
        )
        if today_li >= 10:
            console.print("[yellow]⚠️ LinkedIn daily cap reached (10/day). Falling back to Omnichannel broadcast...[/yellow]")
            return self._execute_original_post(start_time)

        from src.linkedin_automater import LinkedInAutomater
        automater = LinkedInAutomater(headless=True, dry_run=self.safety.dry_run)

        from src.series_manager import AISeriesManager
        series_mgr = AISeriesManager()
        next_day_info = series_mgr.get_next_unpublished_day()

        if next_day_info:
            day_num = next_day_info["day"]
            topic_title = next_day_info["title"]
            level_name = next_day_info.get("level", "Level 1: AI Fundamentals")
            chapter_name = next_day_info.get("chapter", "Core Mental Model")
            console.print(f"[bold cyan]Publishing Series Lesson:[/bold cyan] Day {day_num:02d}: {topic_title}")
            self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1

            try:
                li_text = self.ai.generate_ai_series_lesson(
                    day=day_num,
                    topic=topic_title,
                    level=level_name,
                    chapter=chapter_name
                )
            except Exception as e:
                self.tracker.metrics["lifetime_summary"]["ai_generation_failures"] += 1
                console.print(f"[red]AI Generation Error on Series Day {day_num}: {e}[/red]")
                return False
        else:
            # Fallback to trending topic if all 90 days are done
            trends = self.hunter.get_curated_trending_topics()
            selected_trend = trends[0] if trends else {"title": "Frontier Reasoning Benchmarks", "summary": ""}
            day_num = 0
            topic_title = selected_trend["title"]
            try:
                li_text = self.ai.generate_linkedin_take(selected_trend["title"], selected_trend.get("summary", ""))
            except Exception as e:
                self.tracker.metrics["lifetime_summary"]["ai_generation_failures"] += 1
                console.print(f"[red]AI Generation Error: {e}[/red]")
                self.tracker.record_event(
                    action_type="linkedin_post",
                    status="failed",
                    target_identifier=selected_trend["title"],
                    skip_or_error_reason=f"AI generation failed: {e}",
                    duration_seconds=time.time() - start_time,
                    is_dry_run=self.safety.dry_run
                )
                return False

        console.print(f"[green]Generated LinkedIn Draft:[/green] {li_text[:120]}...")

        if not automater.is_session_available():
            console.print("[yellow]⚠️ LinkedIn session not available. Run 'python main.py login-linkedin'. Skipping.[/yellow]")
            self.tracker.record_event(
                action_type="linkedin_post",
                status="skipped",
                target_identifier=selected_trend["title"],
                content_preview=li_text,
                skip_or_error_reason="LinkedIn session not authenticated",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        ok, msg = automater.post(li_text)
        status = "success" if ok else "failed"
        self.tracker.record_event(
            action_type="linkedin_post",
            status=status,
            target_identifier="LinkedIn B2B",
            content_preview=li_text,
            skip_or_error_reason="" if ok else msg,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )

        if ok:
            console.print(f"[bold blue]✅ {msg}[/bold blue]")
            try:
                self.tracker.history.setdefault("posted_tweets", []).append(f"li:Day {day_num:02d}: {topic_title}")
                self.tracker.save_history()
                if next_day_info:
                    series_mgr.record_published_day(day_num, topic_title, li_text)

                    # --- Automatic Omnichannel Syndication for Daily Series ---
                    # 1. Dev.to Article
                    try:
                        from src.devto_automater import DevToAutomater
                        devto = DevToAutomater()
                        if devto.is_configured():
                            console.print("[bold magenta]Syndicating series lesson to Dev.to...[/bold magenta]")
                            d_ok, d_msg, d_url = devto.create_article(
                                title=f"Day {day_num:02d}: {topic_title}",
                                body_markdown=li_text,
                                series="AI Explained: Zero to Advanced"
                            )
                            if d_ok:
                                console.print(f"[bold green]✅ Dev.to syndicated: {d_url}[/bold green]")
                    except Exception as ex:
                        console.print(f"[dim]Dev.to syndication note: {ex}[/dim]")

                    # 2. Instagram Carousel (5 slides)
                    try:
                        from src.instagram_carousel import InstagramCarouselGenerator
                        from src.instagram_automater import InstagramAutomater
                        ig_automater = InstagramAutomater(headless=True, dry_run=self.safety.dry_run)
                        if ig_automater.is_session_available():
                            console.print("[bold magenta]Rendering & uploading Instagram Carousel...[/bold magenta]")
                            ig_gen = InstagramCarouselGenerator()
                            slides = ig_gen.build_day1_sample() if day_num == 1 else ig_gen.build_day1_sample()
                            ig_caption = f"Day {day_num:02d}: {topic_title}\n\n90 Days. 90 Concepts. One AI Journey. 🎓\n\nSwipe through for the 1-page cheatsheet ➡️\n\n📌 Save this for revision!\n📊 Live 260+ model benchmarks: neubench.netlify.app\n\n#AI #MachineLearning #AIEngineering #Coding"
                            ig_ok, ig_msg = ig_automater.post_carousel(slides, ig_caption)
                            if ig_ok:
                                console.print("[bold green]✅ Instagram carousel published![/bold green]")
                    except Exception as ex:
                        console.print(f"[dim]Instagram syndication note: {ex}[/dim]")

                    # 3. Pinterest Infographic Pin
                    try:
                        from src.pinterest_automater import PinterestAutomater
                        import glob
                        pin_automater = PinterestAutomater(headless=True, dry_run=self.safety.dry_run)
                        if pin_automater.is_session_available():
                            console.print("[bold magenta]Publishing Pin to Pinterest...[/bold magenta]")
                            slides_found = sorted(glob.glob(f"AI_SERIES/CAROUSELS/DAY_{day_num:03d}/*.png"))
                            cover_img = slides_found[0] if slides_found else "AI_SERIES/CAROUSELS/DAY_001/slide_01.png"
                            pin_title = f"Day {day_num:02d}: {topic_title}"
                            pin_desc = f"Part of 90-Day Master Series: AI Explained by NeuBench. Live model benchmarks at neubench.netlify.app"
                            p_ok, p_msg = pin_automater.create_pin(cover_img, pin_title, pin_desc, link="https://neubench.netlify.app")
                            if p_ok:
                                console.print("[bold green]✅ Pinterest Pin published![/bold green]")
                    except Exception as ex:
                        console.print(f"[dim]Pinterest syndication note: {ex}[/dim]")

                    # 4. YouTube Shorts (Animated Video + Dual Subtitles)
                    try:
                        from src.youtube_automater import YouTubeAutomater
                        yt_automater = YouTubeAutomater()
                        if yt_automater.is_authenticated:
                            console.print("[bold magenta]Publishing Animated Short to YouTube Shorts...[/bold magenta]")
                            yt_video = f"AI_SERIES/VIDEOS/DAY_{day_num:03d}/animated_short_day{day_num}.mp4"
                            yt_srt = f"AI_SERIES/VIDEOS/DAY_{day_num:03d}/subtitles_day_{day_num:03d}.srt"
                            if not Path(yt_video).exists():
                                from scripts.render_animated_demo import render_animated_demo
                                render_animated_demo()
                            yt_title = f"Day {day_num:02d}: {topic_title} #Shorts"
                            yt_desc = (
                                f"Day {day_num:02d} of the 90-Day Master Series: AI Explained: Zero to Advanced.\n\n"
                                f"Understand the core engineering foundations of modern AI systems.\n\n"
                                "📊 Live 260+ model benchmarks: https://neubench.netlify.app\n\n"
                                "#Shorts #AI #MachineLearning #DeepLearning #Coding #DataScience"
                            )
                            yt_res = yt_automater.upload_short(video_path=yt_video, title=yt_title, description=yt_desc, srt_path=yt_srt)
                            if yt_res:
                                console.print(f"[bold green]✅ YouTube Short published: {yt_res['url']}[/bold green]")
                    except Exception as ex:
                        console.print(f"[dim]YouTube syndication note: {ex}[/dim]")
            except Exception:
                pass
        else:
            console.print(f"[red]LinkedIn publish failed: {msg}[/red]")

        return ok




    def _execute_threads_post(self, start_time: float) -> bool:
        """Generates a casual Threads post and publishes it via saved session."""
        console.print("[bold magenta]Mode: Threads Auto Post (Community)[/bold magenta]")

        today_th = sum(
            1 for e in self.tracker.metrics.get("recent_events", [])
            if e.get("timestamp", "").startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            and e.get("status") == "success" and not e.get("is_dry_run", False) and e.get("action_type") == "threads_post"
        )
        if today_th >= 10:
            console.print("[yellow]⚠️ Threads daily cap reached (10/day). Falling back to Omnichannel broadcast...[/yellow]")
            return self._execute_original_post(start_time)

        from src.threads_automater import ThreadsAutomater
        automater = ThreadsAutomater(headless=True, dry_run=self.safety.dry_run)

        trends = self.hunter.get_curated_trending_topics()
        pool = trends or []
        if not pool:
            selected_trend = {
                "title": "Frontier Reasoning Drift & Token Efficiency across Claude, Gemini & DeepSeek",
                "summary": "NeuBench telemetry reveals latency and cost differences on long-horizon coding tasks.",
                "company": "NeuBench"
            }
        else:
            selected_trend = None
            for t in pool:
                key = f"th:{t['title']}"
                if key not in self.tracker.history.get("posted_tweets", []):
                    selected_trend = t
                    break
            if not selected_trend:
                selected_trend = random.choice(pool)

        console.print(f"[bold]Trending Topic:[/bold] {selected_trend['title']}")
        self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1

        try:
            th_text = self.ai.generate_threads_take(
                selected_trend["title"],
                selected_trend.get("summary", ""),
                company=selected_trend.get("company", "NeuBench")
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

        if not automater.is_session_available():
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

        ok, msg = automater.post(th_text)
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

        # Outside peak windows: run sniper replies to maintain high engagement without feed spam
        console.print("[dim]Outside peak broadcast windows: Running active sniper reply engagement...[/dim]")
        can_reply, _ = self.safety.can_perform_action("reply", today_counts)
        if can_reply:
            return "reply"

        can_post, _ = self.safety.can_perform_action("post", today_counts)
        if can_post:
            return "post"

        return "repost"

    def _execute_youtube_upload(self, start_time: float) -> bool:
        """Publishes the current AI Series lesson as an animated Short with dual subtitles."""
        console.print("[bold magenta]🎬 Mode: YouTube Shorts Animated Publishing[/bold magenta]")
        from src.youtube_automater import YouTubeAutomater
        from src.series_manager import AISeriesManager

        series_mgr = AISeriesManager()
        next_day = series_mgr.get_next_unpublished_day()
        day_num = next_day["day"] if next_day else 1
        topic_title = next_day["title"] if next_day else "What is Artificial Intelligence?"

        yt = YouTubeAutomater()
        if not yt.is_authenticated:
            console.print("[yellow]YouTube service not authenticated. Run 'python main.py login-youtube'. Skipping.[/yellow]")
            self.tracker.record_event(
                action_type="youtube",
                status="skipped",
                target_identifier=f"Day {day_num}: {topic_title}",
                skip_or_error_reason="YouTube credentials not authenticated",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        yt_video = config.BASE_DIR / f"AI_SERIES/VIDEOS/DAY_{day_num:03d}/animated_short_day{day_num}.mp4"
        yt_srt = config.BASE_DIR / f"AI_SERIES/VIDEOS/DAY_{day_num:03d}/subtitles_day_{day_num:03d}.srt"
        
        if not yt_video.exists():
            console.print(f"[cyan]Rendering Day {day_num} animated short video...[/cyan]")
            try:
                from scripts.render_animated_demo import render_animated_demo
                render_animated_demo()
            except Exception as e:
                console.print(f"[red]Error rendering animated video: {e}[/red]")

        title = f"Day {day_num:02d}: {topic_title} #Shorts"
        desc = (
            f"Day {day_num:02d} of the 90-Day Master Series: AI Explained: Zero to Advanced.\n\n"
            f"Understand the core engineering foundations of modern AI systems.\n\n"
            "📊 Live 260+ model benchmarks: https://neubench.netlify.app\n\n"
            "#Shorts #AI #MachineLearning #DeepLearning #Python #SoftwareEngineering #DataScience"
        )

        if self.safety.dry_run:
            console.print(f"[bold yellow][DRY RUN] Would upload YouTube Short: {title}[/bold yellow]")
            self.tracker.record_event(
                action_type="youtube",
                status="dry_run",
                target_identifier=f"Day {day_num}: {topic_title}",
                content_preview=title,
                duration_seconds=time.time() - start_time,
                is_dry_run=True
            )
            return True

        res = yt.upload_short(video_path=str(yt_video), title=title, description=desc, srt_path=str(yt_srt) if yt_srt.exists() else None)
        ok = res is not None
        status = "success" if ok else "failed"
        url = res.get("url", "") if res else ""
        
        self.tracker.record_event(
            action_type="youtube",
            status=status,
            target_identifier=f"Day {day_num}: {topic_title}",
            content_preview=title,
            skip_or_error_reason="" if ok else "YouTube API upload error",
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )
        if ok:
            console.print(f"[bold green]✅ YouTube Short live: {url}[/bold green]")
        return ok

    def _execute_instagram_carousel(self, start_time: float) -> bool:
        """Renders and publishes the enriched 5-slide technical carousel to Instagram."""
        console.print("[bold magenta]📸 Mode: Instagram Technical Carousel Publishing[/bold magenta]")
        from src.instagram_carousel import InstagramCarouselGenerator
        from src.instagram_automater import InstagramAutomater
        from src.series_manager import AISeriesManager

        series_mgr = AISeriesManager()
        next_day = series_mgr.get_next_unpublished_day()
        day_num = next_day["day"] if next_day else 1
        topic_title = next_day["title"] if next_day else "What is Artificial Intelligence?"

        automater = InstagramAutomater(headless=True, dry_run=self.safety.dry_run)
        if not automater.is_session_available():
            console.print("[yellow]Instagram session not available. Run 'python main.py login-instagram'. Skipping.[/yellow]")
            self.tracker.record_event(
                action_type="instagram",
                status="skipped",
                target_identifier=f"Day {day_num}: {topic_title}",
                skip_or_error_reason="Instagram session not authenticated",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        gen = InstagramCarouselGenerator()
        slides = gen.build_day1_sample()
        caption = (
            f"Day {day_num:02d}: {topic_title}\n\n"
            "90 Days. 90 Concepts. One AI Journey. 🎓\n\n"
            "Swipe through the 1-page engineering cheatsheet ➡️\n\n"
            "📌 Save this post for your revision!\n"
            "📊 Live 260+ model benchmarks: neubench.netlify.app\n\n"
            "#AI #MachineLearning #AIEngineering #Coding #Developers #Tech"
        )
        ok, msg = automater.post_carousel(slides, caption)
        status = "success" if ok else "failed"
        self.tracker.record_event(
            action_type="instagram",
            status=status,
            target_identifier=f"Day {day_num}: {topic_title}",
            content_preview=caption[:100],
            skip_or_error_reason="" if ok else msg,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )
        if ok:
            console.print(f"[bold green]✅ Instagram Carousel published![/bold green]")
        return ok

    def _execute_devto_post(self, start_time: float) -> bool:
        """Publishes the current lesson as a comprehensive article on Dev.to."""
        console.print("[bold magenta]📝 Mode: Dev.to Deep-Dive Article Publishing[/bold magenta]")
        from src.devto_automater import DevToAutomater
        from src.series_manager import AISeriesManager

        series_mgr = AISeriesManager()
        next_day = series_mgr.get_next_unpublished_day()
        day_num = next_day["day"] if next_day else 1
        topic_title = next_day["title"] if next_day else "What is Artificial Intelligence?"
        level_name = next_day.get("level", "Level 1: AI Fundamentals") if next_day else "Level 1"
        chapter_name = next_day.get("chapter", "The Core Mental Model") if next_day else "Core"

        devto = DevToAutomater()
        if not devto.is_configured():
            console.print("[yellow]Dev.to API key not configured. Skipping.[/yellow]")
            return False

        lesson_body = self.ai.generate_ai_series_lesson(
            day=day_num,
            topic=topic_title,
            level=level_name,
            chapter=chapter_name
        )
        title = f"Day {day_num:02d}: {topic_title}"
        ok, msg, url = devto.create_article(title=title, body_markdown=lesson_body, series="AI Explained: Zero to Advanced")
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
        """Publishes an infographic pin to Pinterest."""
        console.print("[bold magenta]📌 Mode: Pinterest Infographic Pin Publishing[/bold magenta]")
        from src.pinterest_automater import PinterestAutomater
        from src.series_manager import AISeriesManager
        import glob

        series_mgr = AISeriesManager()
        next_day = series_mgr.get_next_unpublished_day()
        day_num = next_day["day"] if next_day else 1
        topic_title = next_day["title"] if next_day else "What is Artificial Intelligence?"

        pin_automater = PinterestAutomater(headless=True, dry_run=self.safety.dry_run)
        if not pin_automater.is_session_available():
            console.print("[yellow]Pinterest session not available. Skipping.[/yellow]")
            return False

        slides = sorted(glob.glob(f"AI_SERIES/CAROUSELS/DAY_{day_num:03d}/*.png"))
        cover_img = slides[0] if slides else "AI_SERIES/CAROUSELS/DAY_001/slide_01.png"
        pin_title = f"Day {day_num:02d}: {topic_title}"
        pin_desc = f"Part of the 90-Day Master Series: AI Explained by NeuBench. Save for revision! Live model benchmarks at neubench.netlify.app"
        
        ok, msg = pin_automater.create_pin(cover_img, pin_title, pin_desc, link="https://neubench.netlify.app")
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
