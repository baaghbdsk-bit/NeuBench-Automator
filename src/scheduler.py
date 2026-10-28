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

        if force_action in ("post", "reply", "repost", "bluesky", "linkedin", "reddit", "threads", "omnichannel", "post-all"):

            action_choice = force_action

        else:

            # Distribution: 50% Reply, 15% Repost, 15% Original Post, 8% LinkedIn, 6% Reddit, 6% Threads

            roll = random.randint(1, 100)

            if roll <= 50:

                action_choice = "reply"

            elif roll <= 65:

                action_choice = "repost"

            elif roll <= 80:

                action_choice = "post"

            elif roll <= 88:

                action_choice = "linkedin"

            elif roll <= 94:

                action_choice = "reddit"

            else:

                action_choice = "threads"



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

        elif action_choice == "linkedin":

            return self._execute_linkedin_post(start_time)

        elif action_choice == "reddit":

            return self._execute_reddit_post(start_time)

        elif action_choice == "threads":

            return self._execute_threads_post(start_time)

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

        # 5. Cross-post to Reddit (Independent)
        try:
            from src.reddit_automater import RedditAutomater
            rd_automater = RedditAutomater(headless=False, dry_run=self.safety.dry_run)
            if rd_automater.is_session_available():
                rd_post = self.ai.generate_reddit_post(
                    selected_trend["title"],
                    selected_trend.get("summary", ""),
                    company=selected_trend.get("company", "NeuBench"),
                    subreddit="r/test"
                )
                rd_title = rd_post.get("title", f"Discussion: {selected_trend['title']}")
                rd_body = rd_post.get("body", selected_trend.get("summary", ""))
                rd_ok, rd_msg = rd_automater.post("test", rd_title, rd_body)
                if rd_ok:
                    console.print("[bold orange]🤖 Also published to Reddit (r/test)![/bold orange]")
                    self.tracker.record_event(
                        action_type="reddit_post",
                        status="success",
                        target_identifier="r/test",
                        content_preview=rd_title[:80],
                        duration_seconds=15.0,
                        is_dry_run=self.safety.dry_run
                    )
                else:
                    console.print(f"[yellow]Reddit note: {rd_msg}[/yellow]")
        except Exception as e:
            console.print(f"[dim]Reddit dispatch note: {e}[/dim]")

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
        """Generates a B2B thought-leadership post and publishes it to LinkedIn via saved session."""
        console.print("[bold blue]💼 Mode: LinkedIn Auto Post (B2B Thought Leadership)[/bold blue]")

        # Daily cap: max 2 LinkedIn posts/day
        today_li = sum(
            1 for e in self.tracker.metrics.get("recent_events", [])
            if e.get("timestamp", "").startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            and e.get("status") == "success" and not e.get("is_dry_run", False) and e.get("action_type") == "linkedin_post"
        )
        if today_li >= 2:
            console.print("[yellow]⚠️ LinkedIn daily cap reached (2/2). Skipping.[/yellow]")
            self.tracker.record_event(
                action_type="linkedin_post",
                status="skipped",
                skip_or_error_reason="Daily LinkedIn cap reached (2/day)",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        from src.linkedin_automater import LinkedInAutomater
        automater = LinkedInAutomater(headless=True, dry_run=self.safety.dry_run)

        trends = self.hunter.get_curated_trending_topics()
        # Prefer AI/tech/business-relevant trends for LinkedIn B2B
        preferred = [t for t in trends if t.get("category") in ("ai_tech",) or "NeuBench" in t.get("source", "") or "HackerNews" in t.get("source", "") or "TechCrunch" in t.get("source", "")]
        pool = preferred or trends
        if not pool:
            selected_trend = {
                "title": "Frontier Reasoning Drift & Token Efficiency across Claude, Gemini & DeepSeek",
                "summary": "NeuBench telemetry reveals latency and cost differences on long-horizon coding tasks.",
                "company": "NeuBench"
            }
        else:
            selected_trend = None
            for t in pool:
                key = f"li:{t['title']}"
                if key not in self.tracker.history.get("posted_tweets", []):
                    selected_trend = t
                    break
            if not selected_trend:
                selected_trend = random.choice(pool)

        console.print(f"[bold]Trending Topic:[/bold] {selected_trend['title']}")
        self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1

        try:
            li_text = self.ai.generate_linkedin_take(
                selected_trend["title"],
                selected_trend.get("summary", ""),
                company=selected_trend.get("company", "NeuBench")
            )
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
                self.tracker.history.setdefault("posted_tweets", []).append(f"li:{selected_trend['title']}")
                self.tracker.save_history()
            except Exception:
                pass
        else:
            console.print(f"[red]LinkedIn publish failed: {msg}[/red]")

        return ok


    def _execute_reddit_post(self, start_time: float) -> bool:
        """Generates a community-tailored Reddit post and publishes it via saved session."""
        console.print("[bold orange]Mode: Reddit Auto Post (Community Discussion)[/bold orange]")

        today_rd = sum(
            1 for e in self.tracker.metrics.get("recent_events", [])
            if e.get("timestamp", "").startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            and e.get("status") == "success" and not e.get("is_dry_run", False) and e.get("action_type") == "reddit_post"
        )
        if today_rd >= 1:
            console.print("[yellow]Reddit daily cap reached (1/1). Skipping.[/yellow]")
            self.tracker.record_event(
                action_type="reddit_post",
                status="skipped",
                skip_or_error_reason="Daily Reddit cap reached (1/day)",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        from src.reddit_automater import RedditAutomater
        from src.reddit_client import RedditClient
        automater = RedditAutomater(headless=False, dry_run=self.safety.dry_run)
        rclient = RedditClient()

        subreddits = rclient.get_target_subreddits()
        subreddit = random.choice(subreddits) if subreddits else {"name": "r/LocalLLaMA", "desc": ""}
        sub_name = subreddit.get("name", "r/LocalLLaMA")

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
                key = f"rd:{t['title']}"
                if key not in self.tracker.history.get("posted_tweets", []):
                    selected_trend = t
                    break
            if not selected_trend:
                selected_trend = random.choice(pool)

        console.print(f"[bold]Trending Topic:[/bold] {selected_trend['title']}")
        console.print(f"[bold]Target Subreddit:[/bold] {sub_name}")
        self.tracker.metrics["lifetime_summary"]["ai_generation_requests"] += 1

        try:
            post_data = self.ai.generate_reddit_post(
                selected_trend["title"],
                selected_trend.get("summary", ""),
                company=selected_trend.get("company", "NeuBench"),
                subreddit=sub_name
            )
        except Exception as e:
            self.tracker.metrics["lifetime_summary"]["ai_generation_failures"] += 1
            console.print(f"[red]AI Generation Error: {e}[/red]")
            self.tracker.record_event(
                action_type="reddit_post",
                status="failed",
                target_identifier=selected_trend["title"],
                skip_or_error_reason=f"AI generation failed: {e}",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        title = post_data.get("title", f"Discussion: {selected_trend['title']}")
        body = post_data.get("body", selected_trend.get("summary", ""))
        console.print(f"[green]Generated Reddit Title:[/green] {title}")

        if not automater.is_session_available():
            console.print("[yellow]Reddit session not available. Run 'python main.py login-reddit'. Skipping.[/yellow]")
            self.tracker.record_event(
                action_type="reddit_post",
                status="skipped",
                target_identifier=title,
                content_preview=body,
                skip_or_error_reason="Reddit session not authenticated",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

        ok, msg = automater.post(sub_name, title, body)
        status = "success" if ok else "failed"
        self.tracker.record_event(
            action_type="reddit_post",
            status=status,
            target_identifier=f"{sub_name}",
            content_preview=title,
            skip_or_error_reason="" if ok else msg,
            duration_seconds=time.time() - start_time,
            is_dry_run=self.safety.dry_run
        )

        if ok:
            console.print(f"[bold orange]OK {msg}[/bold orange]")
            try:
                self.tracker.history.setdefault("posted_tweets", []).append(f"rd:{selected_trend['title']}")
                self.tracker.save_history()
            except Exception:
                pass
        else:
            console.print(f"[red]Reddit publish failed: {msg}[/red]")

        return ok


    def _execute_threads_post(self, start_time: float) -> bool:
        """Generates a casual Threads post and publishes it via saved session."""
        console.print("[bold magenta]Mode: Threads Auto Post (Community)[/bold magenta]")

        today_th = sum(
            1 for e in self.tracker.metrics.get("recent_events", [])
            if e.get("timestamp", "").startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            and e.get("status") == "success" and not e.get("is_dry_run", False) and e.get("action_type") == "threads_post"
        )
        if today_th >= 2:
            console.print("[yellow]Threads daily cap reached (2/2). Skipping.[/yellow]")
            self.tracker.record_event(
                action_type="threads_post",
                status="skipped",
                skip_or_error_reason="Daily Threads cap reached (2/day)",
                duration_seconds=time.time() - start_time,
                is_dry_run=self.safety.dry_run
            )
            return False

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

