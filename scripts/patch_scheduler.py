from pathlib import Path

path = Path("src/scheduler.py")
content = path.read_text(encoding="utf-8")

if "from src.bluesky_client import BlueskyClient" not in content:
    content = content.replace(
        "from src.safety import SafetyEngine",
        "from src.safety import SafetyEngine\nfrom src.bluesky_client import BlueskyClient"
    )

if "self.bluesky = BlueskyClient" not in content:
    old_init = "self.twitter = TwitterClient(headless=True, dry_run=self.safety.dry_run)"
    new_init = (
        "self.twitter = TwitterClient(headless=True, dry_run=self.safety.dry_run)\n"
        "        self.bluesky = BlueskyClient(\n"
        "            handle=config.BLUESKY_HANDLE,\n"
        "            app_password=config.BLUESKY_APP_PASSWORD,\n"
        "            dry_run=self.safety.dry_run\n"
        "        )"
    )
    content = content.replace(old_init, new_init)

content = content.replace(
    'if force_action in ("post", "reply", "repost"):',
    'if force_action in ("post", "reply", "repost", "bluesky"):'
)

old_dispatch = 'elif action_choice == "repost":\n            return self._execute_quote_tweet(start_time)'
new_dispatch = (
    'elif action_choice == "repost":\n'
    '            return self._execute_quote_tweet(start_time)\n'
    '        elif action_choice == "bluesky":\n'
    '            return self._execute_bluesky_post(start_time)'
)
content = content.replace(old_dispatch, new_dispatch)

bluesky_method = '''    def _execute_bluesky_post(self, start_time: float) -> bool:
        """Discovers an AI benchmark or frontier tech update and publishes directly to Bluesky."""
        console.print("[bold cyan]🦋 Mode: Autonomous Bluesky Post[/bold cyan]")
        trends = self.hunter.get_curated_trending_topics()
        selected_trend = None
        if trends:
            for t in trends:
                if t["title"] not in self.tracker.history.get("posted_tweets", []):
                    selected_trend = t
                    break
            if not selected_trend:
                selected_trend = random.choice(trends)
        if not selected_trend:
            selected_trend = {
                "title": "Frontier AI Benchmark Discrepancies",
                "summary": "Tracking model performance drift and benchmark evaluations across LLMs on NeuBench."
            }

        bsky_take = self.ai.generate_bluesky_take(
            selected_trend["title"],
            selected_trend.get("summary", ""),
            include_link=True
        )
        console.print(f"[green]Generated Bluesky Take:[/green] {bsky_take}")

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
            console.print("[bold cyan]✅ Successfully published autonomous post to Bluesky![/bold cyan]")
        return ok

    def start_scheduler(self):'''

if "_execute_bluesky_post" not in content:
    content = content.replace("    def start_scheduler(self):", bluesky_method)

path.write_text(content, encoding="utf-8")
print("Patch applied to src/scheduler.py!")
