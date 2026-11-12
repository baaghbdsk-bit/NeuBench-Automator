import sys
import subprocess
import time
from pathlib import Path

# Auto-switch to virtualenv python if invoked via global python without venv activated
_BASE_DIR = Path(__file__).resolve().parent
_VENV_PYTHON = _BASE_DIR / "venv" / "Scripts" / "python.exe"
if _VENV_PYTHON.exists() and Path(sys.executable).resolve() != _VENV_PYTHON.resolve():
    try:
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
    parser = argparse.ArgumentParser(
        description="NeuBench Automater: Ultra-Fast Omnichannel Suite for 𝕏, LinkedIn, and Bluesky"
    )
    parser.add_argument(
        "action", 
        choices=[
            "start", "run-once", "post-all", "omnichannel",
            "post", "reply", "repost", "mentions", "debate-sniper", "indian-monitor", "indian-queue", "indian-publish", "indian-summary",
            "linkedin", "linkedin-replies", "linkedin-peers",
            "bluesky", "bluesky-replies",
            "login", "login-linkedin", "test", "metrics"
        ],
        help="Action to execute"
    )
    parser.add_argument("--url", type=str, default="", help="Target tweet URL (for 'reply' or 'repost' action)")
    parser.add_argument("--text", type=str, default="", help="Custom text for direct post")
    parser.add_argument("--dry-run", action="store_true", help="Run in simulation mode without publishing live")
    parser.add_argument("--id", type=str, default="", help="Target opportunity ID for approval")
    parser.add_argument("--topic", type=str, default="", help="Custom topic for LinkedIn or other posts")

    args = parser.parse_args()

    if args.action == "indian-summary":
        from src.indian_influence_engine import IndianEngagementEngine
        engine = IndianEngagementEngine()
        summary = engine.generate_audit_summary()
        console.print(Panel(json.dumps(summary, indent=2), title="🇮🇳 Indian Influence Discovery Audit"))
        return

    if args.action == "indian-queue":
        from src.indian_influence_engine import OpportunityQueueManager
        qm = OpportunityQueueManager()
        data = qm.load_queue()
        console.print(f"\n[bold cyan]🇮🇳 Indian Engagement Opportunity Queue ({len(data.get('opportunities', []))} items):[/bold cyan]")
        for o in data.get("opportunities", []):
            st_color = "yellow" if o["status"] == "pending_approval" else "green" if o["status"] == "approved" else "dim"
            console.print(f"[{st_color}]• [{o['status'].upper()}][/{st_color}] @{o['author']} ({o['category']}) | ID: {o['id']}")
            console.print(f"   [white]Target:[/white] {o['tweet_text'][:70]}...")
            console.print(f"   [cyan]Reply:[/cyan] {o['suggested_reply']}")
        return

    if args.action == "indian-monitor":
        from src.indian_influence_engine import IndianEngagementEngine
        engine = IndianEngagementEngine()
        engine.monitor_and_discover_opportunities(sample_size=4)
        return

    if args.action == "indian-publish":
        from src.indian_influence_engine import IndianEngagementEngine
        engine = IndianEngagementEngine()
        engine.process_approved_queue(dry_run=args.dry_run, max_actions=1)
        return

    if args.action == "metrics":
        display_metrics()
        return

    if args.action == "login":
        from scripts.login_browser import login_and_save_session
        login_and_save_session()
        return

    if args.action == "login-linkedin":
        from scripts.login_linkedin import login_linkedin
        login_linkedin()
        return

    if args.action == "test":
        from scripts.test_pipeline import test_pipeline
        test_pipeline()
        return

    from src.scheduler import AutomaterEngine
    engine = AutomaterEngine(dry_run=args.dry_run)

    if args.action in ("start",):
        console.print("[bold green]Starting autonomous continuous schedule (every ~3 hours across 𝕏, LinkedIn, Bluesky)...[/bold green]")
        engine.start_scheduler()

    elif args.action in ("run-once", "post-all", "omnichannel"):
        console.print(f"[bold cyan]🚀 Running 3-Hour Broadcast Cycle across 𝕏, LinkedIn & Bluesky (Dry Run: {args.dry_run})...[/bold cyan]")
        results = engine.run_three_hour_omnichannel_cycle()
        if not any(results.values()) and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "post":
        if args.text:
            ok = engine.execute_x_custom_post(args.text)
        else:
            ok = engine.run_single_cycle(force_action="post")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "reply":
        if args.url:
            ok = engine.execute_x_reply(args.url, args.text or "Viral debate")
        else:
            ok = engine.run_single_cycle(force_action="reply")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "repost":
        if args.url:
            ok = engine.execute_x_quote(args.url, args.text or "Viral debate")
        else:
            ok = engine.run_single_cycle(force_action="repost")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "mentions":
        ok = engine.run_single_cycle(force_action="mentions")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "debate-sniper":
        ok = engine.run_single_cycle(force_action="debate-sniper")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "linkedin":
        if args.topic:
            ok = engine.execute_linkedin_topic_post(args.topic)
        elif args.text:
            ok = engine.execute_linkedin_custom_post(args.text)
        else:
            ok = engine.run_single_cycle(force_action="linkedin")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "linkedin-replies":
        ok = engine.run_single_cycle(force_action="linkedin-replies")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "linkedin-peers":
        ok = engine.run_single_cycle(force_action="linkedin-peers")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "bluesky":
        if args.text:
            ok = engine.execute_bluesky_custom_post(args.text)
        else:
            ok = engine.run_single_cycle(force_action="bluesky")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

    elif args.action == "bluesky-replies":
        ok = engine.run_single_cycle(force_action="bluesky-replies")
        if not ok and not engine.safety.dry_run:
            sys.exit(1)

if __name__ == "__main__":
    main()
