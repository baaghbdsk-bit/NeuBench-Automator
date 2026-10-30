import sys
import subprocess
from pathlib import Path

# Auto-switch to virtualenv python if invoked via global python without venv activated
_BASE_DIR = Path(__file__).resolve().parent
_VENV_PYTHON = _BASE_DIR / "venv" / "Scripts" / "python.exe"
if _VENV_PYTHON.exists() and Path(sys.executable).resolve() != _VENV_PYTHON.resolve():
    try:
        # Re-execute seamlessly inside the virtual environment
        sys.exit(subprocess.call([str(_VENV_PYTHON)] + sys.argv))
    except Exception:
        pass

import argparse
import json

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def display_metrics():
    metrics_path = Path("trial_metrics.json")
    if not metrics_path.exists():
        console.print("[yellow]No trial_metrics.json found yet.[/yellow]")
        return

    try:
        with open(metrics_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data.get("trial_meta", {})
        summary = data.get("lifetime_summary", {})
        events = data.get("recent_events", [])

        console.print("\n" + "="*60, style="bold cyan")
        console.print("📊 24-48 HOUR TRIAL ACTIVITY METRICS", style="bold green")
        console.print(f"Trial Start (UTC): {meta.get('trial_start_utc')} | Last Updated: {meta.get('last_updated')}")
        console.print("="*60, style="bold cyan")

        table = Table(title="Lifetime Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green", justify="right")

        for k, v in summary.items():
            table.add_row(k.replace("_", " ").title(), str(v))
        console.print(table)

        if events:
            ev_table = Table(title="Recent 5 Events")
            ev_table.add_column("Timestamp (UTC)", style="dim")
            ev_table.add_column("Action", style="yellow")
            ev_table.add_column("Status", style="bold")
            ev_table.add_column("Target / Preview", style="white")

            for ev in events[-5:]:
                st_style = "green" if ev.get("status") == "success" else "yellow" if ev.get("status") == "skipped" else "red"
                ev_table.add_row(
                    ev.get("timestamp", "")[:19],
                    ev.get("action_type", ""),
                    f"[{st_style}]{ev.get('status')}[/{st_style}]",
                    (ev.get("target") or ev.get("content_preview", ""))[:45]
                )
            console.print(ev_table)

    except Exception as e:
        console.print(f"[red]Error reading metrics: {e}[/red]")

def main():
    parser = argparse.ArgumentParser(description="NeuBench Automater: Omnichannel Social Growth Suite for NeuBench (𝕏, Bluesky, LinkedIn, Threads)")
    parser.add_argument(
        "action", 
        choices=["login", "login-linkedin", "login-threads", "login-instagram", "login-youtube", "login-pinterest", "test", "run-once", "start", "post", "reply", "repost", "bluesky", "linkedin", "threads", "instagram", "devto", "pinterest", "youtube", "render-video", "update-profile", "metrics", "dashboard", "ui", "omnichannel", "post-all"], 
        help="Action: 'dashboard', 'youtube', 'render-video', 'login-youtube', 'bluesky', 'linkedin', 'threads', 'instagram', 'devto', 'pinterest', 'run-once', 'post', 'start'"
    )
    parser.add_argument("--url", type=str, default="", help="Target tweet URL (for 'reply' or 'repost' action)")
    parser.add_argument("--text", type=str, default="", help="Custom text (for 'post', 'reply', 'repost', 'bluesky', or 'linkedin')")
    parser.add_argument("--dry-run", action="store_true", help="Run without publishing live")
    parser.add_argument("--name", type=str, default="vishnu rot", help="Display Name for profile")
    parser.add_argument("--bio", type=str, default="Tech, markets & the absurd reality of modern work. Calling out what everyone thinks but won't tweet. | Building in public.", help="Bio for profile")
    parser.add_argument("--location", type=str, default="Bengaluru / Earth", help="Location for profile")
    parser.add_argument("--avatar", type=str, default="", help="Avatar image path for profile")
    parser.add_argument("--header", type=str, default="", help="Header banner image path for profile")

    args = parser.parse_args()

    if args.action == "metrics":
        display_metrics()
        return

    if args.action in ("dashboard", "ui"):
        import webbrowser
        import uvicorn
        console.print("\n[bold cyan]🚀 Starting NeuBench Omnichannel Dashboard on http://127.0.0.1:8000[/bold cyan]")
        console.print("[dim]Press Ctrl+C to stop the dashboard server[/dim]\n")
        try:
            webbrowser.open("http://127.0.0.1:8000")
        except Exception:
            pass
        uvicorn.run("src.web.app:app", host="127.0.0.1", port=8000, reload=False)
        return

    if args.action == "bluesky":
        import config
        from src.bluesky_client import BlueskyClient
        from src.ai_generator import AIGenerator
        client = BlueskyClient(
            handle=config.BLUESKY_HANDLE,
            app_password=config.BLUESKY_APP_PASSWORD,
            dry_run=args.dry_run
        )
        if args.text:
            text = args.text
        else:
            ai = AIGenerator()
            console.print("[cyan]Generating high-signal AI benchmark take for Bluesky...[/cyan]")
            text = ai.generate_bluesky_take(
                title="DeepSeek vs Llama Inference & Quantization Benchmarks",
                summary="Tracking 42% latency reduction and throughput tradeoffs on NeuBench.",
                company="NeuBench"
            )
        console.print(f"[bold green]Bluesky Post Draft:[/bold green]\n{text}\n")
        ok, msg = client.post(text)
        if ok:
            console.print(f"[bold cyan]✅ {msg}[/bold cyan]")
        else:
            console.print(f"[bold red]❌ {msg}[/bold red]")

    elif args.action == "login-linkedin":
        from scripts.login_linkedin import login_linkedin
        login_linkedin()

    elif args.action == "linkedin":
        import webbrowser
        from src.ai_generator import AIGenerator
        from src.linkedin_client import LinkedInClient
        from src.linkedin_automater import LinkedInAutomater

        automater = LinkedInAutomater(headless=True, dry_run=args.dry_run)
        client = LinkedInClient()

        if args.text:
            text = args.text
        else:
            ai = AIGenerator()
            console.print("[cyan]Generating high-authority B2B thought-leadership post for LinkedIn...[/cyan]")
            text = ai.generate_linkedin_take(
                title="Frontier Reasoning Drift & Token Efficiency across Claude 3.5, Gemini 2.0 & DeepSeek-V3",
                summary="NeuBench telemetry reveals significant latency and cost differences when evaluating long-horizon coding tasks on quantized vs dense weights.",
                company="NeuBench"
            )

        console.print(Panel(text, title="[bold blue]LinkedIn B2B Thought-Leadership Draft[/bold blue]", border_style="blue"))

        # If autonomous session exists, publish autonomously!
        if automater.is_session_available():
            console.print("\n[bold cyan]🤖 Saved LinkedIn session detected! Publishing autonomously...[/bold cyan]")
            ok, msg = automater.post(text)
            if ok:
                console.print(f"[bold green]✅ {msg}[/bold green]")
            else:
                console.print(f"[yellow]⚠️ Autonomous attempt note: {msg}[/yellow]")
                share_url = client.generate_share_url(text)
                console.print(f"[dim]Falling back to 1-Click Composer URL: {share_url}[/dim]")
        else:
            share_url = client.generate_share_url(text)
            console.print(f"[bold green]🚀 1-Click LinkedIn Composer URL:[/bold green]\n{share_url}\n")
            try:
                webbrowser.open(share_url)
                console.print("[dim]Opened LinkedIn composer in your default browser.[/dim]")
            except Exception:
                pass

    elif args.action == "login":
        from scripts.login_browser import login_and_save_session
        login_and_save_session()

    elif args.action == "login-threads":
        from scripts.login_threads import login_threads
        login_threads()

    elif args.action == "login-instagram":
        from scripts.login_instagram import login_instagram
        login_instagram()
        
    elif args.action == "test":
        from scripts.test_pipeline import test_pipeline
        test_pipeline()
        
    elif args.action == "post":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        if args.text:
            engine.twitter.post_tweet(args.text)
        else:
            engine.run_single_cycle(force_action="post")

    elif args.action == "reply":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        if args.url:
            tweet_text = args.text or "Viral debate"
            reply = engine.ai.generate_sniper_reply("tweet_author", tweet_text)
            console.print(f"[green]Posting reply:[/green] {reply}")
            engine.twitter.post_reply(args.url, reply)
        else:
            engine.run_single_cycle(force_action="reply")

    elif args.action == "repost":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        if args.url:
            tweet_text = args.text or "Viral debate"
            commentary = engine.ai.generate_quote_tweet_commentary("tweet_author", tweet_text)
            console.print(f"[green]Posting quote-tweet:[/green] {commentary}")
            engine.twitter.post_quote_tweet(args.url, commentary)
        else:
            engine.run_single_cycle(force_action="repost")

    elif args.action == "update-profile":
        from scripts.update_profile import update_x_profile
        update_x_profile(
            name=args.name,
            bio=args.bio,
            location=args.location,
            avatar_path=args.avatar or None,
            header_path=args.header or None
        )

    elif args.action == "threads":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        engine.run_single_cycle(force_action="threads")

    elif args.action == "login-pinterest":
        from scripts.login_pinterest import login_pinterest
        login_pinterest()

    elif args.action == "login-youtube":
        from scripts.login_youtube import login_youtube
        login_youtube()

    elif args.action == "render-video":
        from scripts.render_animated_demo import render_animated_demo
        console.print("[magenta]Rendering high-production animated short...[/magenta]")
        render_animated_demo()
        console.print("[bold green]✅ Animated short rendered in AI_SERIES/VIDEOS/DAY_001/[/bold green]")

    elif args.action == "youtube":
        from src.youtube_automater import YouTubeAutomater
        console.print("[magenta]Uploading latest animated short to YouTube Shorts (@neubench)...[/magenta]")
        yt = YouTubeAutomater()
        video_path = "AI_SERIES/VIDEOS/DAY_001/animated_short_day1.mp4"
        srt_path = "AI_SERIES/VIDEOS/DAY_001/subtitles_day_001.srt"
        if not Path(video_path).exists():
            from scripts.render_animated_demo import render_animated_demo
            console.print("[yellow]Video not found, rendering now...[/yellow]")
            render_animated_demo()

        title = "Day 01: What is AI? (Rules-Based Code vs Learned Behavior) #Shorts"
        desc = (
            "Day 01 of the 90-Day Master Series: AI Explained: Zero to Advanced.\n\n"
            "Understand the core mental model of modern AI engineering: moving from hardcoded deterministic "
            "rules to continuous weight optimization.\n\n"
            "📊 Live 260+ model benchmarks: https://neubench.netlify.app\n\n"
            "#Shorts #AI #MachineLearning #DeepLearning #Python #SoftwareEngineering #DataScience"
        )
        res = yt.upload_short(video_path=video_path, title=title, description=desc, srt_path=srt_path)
        if res:
            console.print(f"[bold green]✅ Published live to YouTube: {res['url']}[/bold green]")
        else:
            console.print("[bold red]❌ Failed to upload to YouTube. Check credentials.[/bold red]")

    elif args.action == "pinterest":
        import glob
        from src.pinterest_automater import PinterestAutomater
        from src.series_manager import AISeriesManager
        console.print("[magenta]Publishing latest AI Series Pin to Pinterest...[/magenta]")
        automater = PinterestAutomater(headless=False, dry_run=args.dry_run)
        slides = sorted(glob.glob('AI_SERIES/CAROUSELS/DAY_001/*.png'))
        if not slides:
            from src.instagram_carousel import InstagramCarouselGenerator
            generator = InstagramCarouselGenerator()
            slides = generator.build_day1_sample()
        cover_image = slides[0]
        title = "Day 01: What is AI? (Rules-Based vs. Learned Behavior)"
        desc = "Part of the 90-Day Master Series: AI Explained: Zero to Advanced by NeuBench. Save this pin for your revision notes! Live AI model benchmarks at neubench.netlify.app"
        ok, msg = automater.create_pin(image_path=cover_image, title=title, description=desc, link="https://neubench.netlify.app")
        if ok:
            console.print(f"[bold green]✅ {msg}[/bold green]")
        else:
            console.print(f"[bold red]❌ {msg}[/bold red]")

    elif args.action == "devto":
        from src.devto_automater import DevToAutomater
        from src.series_manager import AISeriesManager
        from src.ai_generator import AIGenerator
        console.print("[magenta]Publishing latest AI Series lesson to Dev.to (@neubench)...[/magenta]")
        manager = AISeriesManager()
        next_topic = manager.get_next_unpublished_day()
        if not next_topic:
            next_topic = {"day": 1, "title": "What is Artificial Intelligence? (Rules-based Code vs. Learned Behavior)", "level": "Level 1", "chapter": "The Core Mental Model"}
        ai = AIGenerator()
        lesson_body = ai.generate_ai_series_lesson(
            day=next_topic["day"],
            topic_title=next_topic["title"],
            level=next_topic["level"],
            chapter=next_topic["chapter"]
        )
        automater = DevToAutomater()
        title = f"Day {next_topic['day']:02d}: {next_topic['title']}"
        ok, msg, url = automater.create_article(title=title, body_markdown=lesson_body, series="AI Explained: Zero to Advanced")
        if ok:
            console.print(f"[bold green]✅ {msg}: {url}[/bold green]")
        else:
            console.print(f"[bold red]❌ {msg}[/bold red]")

    elif args.action == "instagram":
        from src.instagram_carousel import InstagramCarouselGenerator
        from src.instagram_automater import InstagramAutomater
        console.print("[magenta]Rendering latest AI Series carousel slides for Instagram (@neubench)...[/magenta]")
        generator = InstagramCarouselGenerator()
        image_paths = generator.build_day1_sample()
        automater = InstagramAutomater(headless=False, dry_run=args.dry_run)
        caption = "Day 01: What is Artificial Intelligence? (Rules-Based Code vs. Learned Behavior)\n\n90 Days. 90 Concepts. One AI Journey.\n\nSwipe through the 1-page cheatsheet ➡️\n\n📌 Save this post for your revision!\n📊 Live 260+ model benchmarks: neubench.netlify.app\n\n#AI #MachineLearning #AIEngineering #Coding #Developers"
        ok, msg = automater.post_carousel(image_paths, caption)
        if ok:
            console.print(f"[bold green]✅ {msg}[/bold green]")
        else:
            console.print(f"[bold red]❌ {msg}[/bold red]")

    elif args.action in ("omnichannel", "post-all"):
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        console.print("[bold cyan]🚀 Triggering Omnichannel Broadcast Across All Platforms...[/bold cyan]")
        engine._execute_original_post(time.time())

    elif args.action in ("start", "run-once"):
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        if args.action == "run-once":
            console.print("[cyan]Running single autonomous cycle across all platforms...[/cyan]")
            engine.run_single_cycle()
        else:
            console.print("[bold green]Starting autonomous continuous schedule...[/bold green]")
            engine.start_scheduler()

if __name__ == "__main__":
    main()
