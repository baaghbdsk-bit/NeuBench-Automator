import sys
import argparse
import json
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table

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
    parser = argparse.ArgumentParser(description="NeuBench X-Post Automator: Omnichannel Social Growth Suite for NeuBench (𝕏, Bluesky, LinkedIn, Threads)")
    parser.add_argument(
        "action", 
        choices=["login", "test", "run-once", "start", "post", "reply", "repost", "update-profile", "metrics", "dashboard", "ui"], 
        help="Action: 'dashboard' (launch UI), 'run-once', 'post', 'reply', 'repost', 'metrics', 'login', 'test', 'start'"
    )
    parser.add_argument("--url", type=str, default="", help="Target tweet URL (for 'reply' or 'repost' action)")
    parser.add_argument("--text", type=str, default="", help="Custom text (for 'post', 'reply', or 'repost')")
    parser.add_argument("--dry-run", action="store_true", help="Run without publishing live to X")
    parser.add_argument("--name", type=str, default="vishnu rot", help="Display Name for profile")
    parser.add_argument("--bio", type=str, default="Tech, markets & the absurd reality of modern work. Calling out what everyone thinks but won't tweet. | Building in public.", help="Bio for profile")
    parser.add_argument("--location", type=str, default="Bengaluru / Earth", help="Location for profile")

    args = parser.parse_args()

    if args.action == "metrics":
        display_metrics()
        return

    if args.action in ("dashboard", "ui"):
        import webbrowser
        import uvicorn
        console.print("\n[bold cyan]🚀 Starting NeuBench X-Post Automator Dashboard on http://127.0.0.1:8000[/bold cyan]")
        console.print("[dim]Press Ctrl+C to stop the dashboard server[/dim]\n")
        try:
            webbrowser.open("http://127.0.0.1:8000")
        except Exception:
            pass
        uvicorn.run("src.web.app:app", host="127.0.0.1", port=8000, reload=False)
        return

    if args.action == "login":
        from scripts.login_browser import login_and_save_session
        login_and_save_session()
        
    elif args.action == "test":
        from scripts.test_generation import test_pipeline
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
        update_x_profile(name=args.name, bio=args.bio, location=args.location)

    elif args.action == "run-once":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        engine.run_single_cycle()
        
    elif args.action == "start":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        engine.start_scheduler()

if __name__ == "__main__":
    main()
