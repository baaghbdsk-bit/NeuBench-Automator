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
        choices=["login", "login-linkedin", "login-reddit", "login-threads", "login-instagram", "login-youtube", "login-pinterest", "test", "run-once", "start", "post", "reply", "repost", "bluesky", "linkedin", "linkedin-replies", "linkedin-peers", "threads", "reddit", "instagram", "devto", "pinterest", "youtube", "render-video", "update-profile", "metrics", "dashboard", "ui", "omnichannel", "post-all"],
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
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        if args.text:
            ok = engine.execute_bluesky_custom_post(args.text)
        else:
            ok = engine.run_single_cycle(force_action="bluesky")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "login-linkedin":
        from scripts.login_linkedin import login_linkedin
        login_linkedin()

    elif args.action == "linkedin":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        if args.text:
            ok = engine.execute_linkedin_custom_post(args.text)
        else:
            ok = engine.run_single_cycle(force_action="linkedin")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "linkedin-replies":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        ok = engine.run_single_cycle(force_action="linkedin-replies")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "linkedin-peers":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        ok = engine.run_single_cycle(force_action="linkedin-peers")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "login":
        from scripts.login_browser import login_and_save_session
        login_and_save_session()

    elif args.action == "login-threads":
        from scripts.login_threads import login_threads
        login_threads()

    elif args.action == "login-reddit":
        from scripts.login_reddit import login_reddit
        if not login_reddit():
            sys.exit(1)

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
            ok = engine.execute_x_custom_post(args.text)
        else:
            ok = engine.run_single_cycle(force_action="post")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "reply":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        if args.url:
            ok = engine.execute_x_reply(args.url, args.text or "Viral debate")
        else:
            ok = engine.run_single_cycle(force_action="reply")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "repost":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        if args.url:
            ok = engine.execute_x_quote(args.url, args.text or "Viral debate")
        else:
            ok = engine.run_single_cycle(force_action="repost")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

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
        ok = engine.run_single_cycle(force_action="threads")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "reddit":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        ok = engine.run_single_cycle(force_action="reddit")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

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
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        ok = engine.run_single_cycle(force_action="youtube")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "pinterest":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        ok = engine.run_single_cycle(force_action="pinterest")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "devto":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        ok = engine.run_single_cycle(force_action="devto")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "instagram":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        ok = engine.run_single_cycle(force_action="instagram")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action in ("omnichannel", "post-all"):
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        console.print("[bold cyan]🚀 Triggering Omnichannel Broadcast Across All Platforms...[/bold cyan]")
        ok = engine.run_single_cycle(force_action="post")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action in ("start", "run-once"):
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=args.dry_run)
        if args.action == "run-once":
            console.print("[cyan]Running single autonomous cycle across all platforms...[/cyan]")
            ok = engine.run_single_cycle()
            if not ok and not engine.safety.dry_run:
                sys.exit(1)
        else:
            console.print("[bold green]Starting autonomous continuous schedule...[/bold green]")
            engine.start_scheduler()

if __name__ == "__main__":
    main()
