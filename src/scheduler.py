import sys
import time
import json
import random
from datetime import datetime
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

console = Console()

# Target high-engagement accounts for explosive reach (Indian + Global giants)
VIRAL_ACCOUNTS = [
    # Top Indian Reach & Debate Accounts
    "IndianTechGuide",
    "peakbengaluru",
    "ANI",
    "NDTV",
    "thetanmay",
    "kunalb11",
    "Zomato",
    # Global Heavyweights
    "elonmusk",
    "sama",
    "PopBase",
    "WatcherGuru",
    "unusual_whales"
]

class AutomaterEngine:
    def __init__(self):
        self.hunter = TrendHunter()
        self.ai = AIGenerator()
        self.twitter = TwitterClient(headless=True)
        self.history_file = config.BASE_DIR / "post_history.json"
        self.history = self._load_history()

    def _load_history(self) -> dict:
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"posted_tweets": [], "replied_urls": []}

    def _save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            console.print(f"[red]Error saving history: {e}[/red]")

    def run_single_cycle(self) -> bool:
        """Executes one automated action: either an original debate take or a sniper reply."""
        console.print(f"\n[cyan]⏱️  Cycle triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/cyan]")
        
        is_reply = random.randint(1, 100) <= config.REPLY_PERCENTAGE
        
        if is_reply:
            return self._execute_sniper_reply()
        else:
            return self._execute_original_post()

    def _execute_sniper_reply(self) -> bool:
        """Finds a viral account, extracts latest tweet, and replies with high-engagement AI take."""
        console.print("[bold yellow]🎯 Mode: Sniper Reply on Viral Account[/bold yellow]")
        
        # Pick random viral account
        account = random.choice(VIRAL_ACCOUNTS)
        console.print(f"[dim]Checking latest tweet from @{account}...[/dim]")
        
        tweet_data = self.twitter.get_latest_tweet_from_account(account)
        tweet_url = tweet_data.get("tweet_url")
        tweet_text = tweet_data.get("tweet_text")
        
        if not tweet_url or not tweet_text:
            console.print("[yellow]Could not find suitable tweet. Falling back to original post...[/yellow]")
            return self._execute_original_post()
            
        if tweet_url in self.history["replied_urls"]:
            console.print(f"[dim]Already replied to {tweet_url}. Skipping...[/dim]")
            return False

        console.print(f"[bold]Target Tweet:[/bold] {tweet_text[:80]}...")
        reply_content = self.ai.generate_sniper_reply(account, tweet_text)
        console.print(f"[green]Generated Reply:[/green] {reply_content}")

        success = self.twitter.post_reply(tweet_url, reply_content)
        if success:
            self.history["replied_urls"].append(tweet_url)
            self._save_history()
            console.print("[bold green]✅ Successfully sniped reply![/bold green]")
        return success

    def _execute_original_post(self) -> bool:
        """Discovers trending topics and posts a polarizing hot take."""
        console.print("[bold magenta]🚀 Mode: Original Debate Hot Take[/bold magenta]")
        
        trends = self.hunter.get_curated_trending_topics()
        if not trends:
            console.print("[red]No trends found to post about.[/red]")
            return False
            
        # Select an unused trend
        selected_trend = None
        for t in trends:
            if t["title"] not in self.history["posted_tweets"]:
                selected_trend = t
                break
                
        if not selected_trend:
            selected_trend = trends[0]

        console.print(f"[bold]Trending Topic:[/bold] {selected_trend['title']}")
        hot_take = self.ai.generate_hot_take(
            selected_trend["title"], 
            selected_trend.get("summary", "")
        )
        console.print(f"[green]Generated Hot Take:[/green] {hot_take}")

        success = self.twitter.post_tweet(hot_take)
        if success:
            self.history["posted_tweets"].append(selected_trend["title"])
            self._save_history()
            console.print("[bold green]✅ Successfully published tweet![/bold green]")
        return success

    def start_scheduler(self):
        """Runs the continuous loop with randomized intervals to avoid bot detection."""
        console.print("\n" + "="*60, style="bold cyan")
        console.print("🤖 X-Post-Automater Active & Running", style="bold green")
        console.print(f"Target: ~{config.POSTS_PER_DAY} posts/day ({config.REPLY_PERCENTAGE}% sniper replies)", style="yellow")
        console.print("="*60 + "\n", style="bold cyan")

        while True:
            try:
                self.run_single_cycle()
            except Exception as e:
                console.print(f"[bold red]Cycle Error: {e}[/bold red]")

            # Random sleep interval between min and max configured minutes
            sleep_minutes = random.randint(
                config.POST_INTERVAL_MIN_MINUTES,
                config.POST_INTERVAL_MAX_MINUTES
            )
            console.print(f"\n[dim]💤 Sleeping for {sleep_minutes} minutes before next post...[/dim]\n")
            time.sleep(sleep_minutes * 60)
