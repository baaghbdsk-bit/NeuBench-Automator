import sys
import argparse

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console

console = Console()

def main():
    parser = argparse.ArgumentParser(description="X-Post-Automater: Maximize reach and monetization on X.")
    parser.add_argument(
        "action", 
        choices=["login", "test", "run-once", "start", "post", "reply", "update-profile"], 
        help="Action: 'login', 'test', 'run-once', 'start', 'post', 'reply', 'update-profile'"
    )
    parser.add_argument("--url", type=str, default="", help="Target tweet URL (for 'reply' action)")
    parser.add_argument("--text", type=str, default="", help="Custom text (for 'post' or 'reply')")
    parser.add_argument("--name", type=str, default="Vivek | Unfiltered", help="Display Name for profile")
    parser.add_argument("--bio", type=str, default="Tech, markets & the absurd reality of modern work. Calling out what everyone thinks but won't tweet. | Building in public.", help="Bio for profile")
    parser.add_argument("--location", type=str, default="Bengaluru / Earth", help="Location for profile")

    args = parser.parse_args()

    if args.action == "login":
        from scripts.login_browser import login_and_save_session
        login_and_save_session()
        
    elif args.action == "test":
        from scripts.test_generation import test_pipeline
        test_pipeline()
        
    elif args.action == "post":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine()
        if args.text:
            engine.twitter.post_tweet(args.text)
        else:
            engine._execute_original_post()

    elif args.action == "reply":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine()
        if args.url:
            tweet_text = args.text or "Viral debate"
            reply = engine.ai.generate_sniper_reply("tweet_author", tweet_text)
            console.print(f"[green]Posting reply:[/green] {reply}")
            engine.twitter.post_reply(args.url, reply)
        else:
            engine._execute_sniper_reply()

    elif args.action == "update-profile":
        from scripts.update_profile import update_x_profile
        update_x_profile(name=args.name, bio=args.bio, location=args.location)

    elif args.action == "run-once":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine()
        engine.run_single_cycle()
        
    elif args.action == "start":
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine()
        engine.start_scheduler()

if __name__ == "__main__":
    main()
