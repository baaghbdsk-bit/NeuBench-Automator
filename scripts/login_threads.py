import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from playwright.sync_api import sync_playwright
import config

console = Console()

def login_threads():
    console.print("\n" + "="*60, style="bold magenta")
    console.print("🧵 THREADS AUTONOMOUS BROWSER SESSION SETUP", style="bold white on magenta")
    console.print("="*60, style="bold magenta")
    console.print("\n[cyan]A visible Chrome/Chromium browser window will open now.[/cyan]")
    console.print("[yellow]1. Log in with your Instagram or Threads credentials.[/yellow]")
    console.print("[yellow]2. Complete any 2FA or verification prompt if asked.[/yellow]")
    console.print("[green]3. Once you reach your Threads feed, this script will save your session![/green]\n")

    user_data_dir = config.BASE_DIR / "threads_session"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(user_data_dir),
            "headless": False,
            "viewport": {"width": 1280, "height": 800},
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--start-maximized"
            ]
        }
        try:
            context = p.chromium.launch_persistent_context(**launch_kwargs, channel="chrome")
        except Exception:
            context = p.chromium.launch_persistent_context(**launch_kwargs)

        page = context.pages[0] if context.pages else context.new_page()

        try:
            console.print("[dim]Navigating to https://www.threads.net/login ...[/dim]")
            page.goto("https://www.threads.net/login", wait_until="domcontentloaded", timeout=45000)

            console.print("[bold yellow]Waiting for you to log in... (Checking every 2 seconds)[/bold yellow]")

            max_wait_seconds = 300
            start_wait = time.time()
            logged_in = False

            while time.time() - start_wait < max_wait_seconds:
                # 1. Check cookies for Instagram/Threads session
                try:
                    cookies = context.cookies()
                    if any(c.get("name") in ("sessionid", "ds_user_id") for c in cookies):
                        logged_in = True
                except Exception:
                    pass

                # 2. Check if reached main feed
                current_url = page.url.lower()
                if "login" not in current_url and ("threads.net" in current_url):
                    try:
                        # Feed navigation bar or profile tab
                        if page.locator('svg[aria-label="Home"], svg[aria-label="Profile"], a[href*="/@"]').first.is_visible():
                            logged_in = True
                            break
                    except Exception:
                        pass
                    if logged_in:
                        break

                time.sleep(2)

            if logged_in:
                console.print("\n[bold green]🎉 SUCCESS! Logged into Threads successfully![/bold green]")
                time.sleep(2)
                console.print(f"[bold cyan]✅ Session saved into: {user_data_dir}[/bold cyan]")
                return True
            else:
                console.print("\n[red]Login timed out after 5 minutes. Please try again.[/red]")
                return False

        except Exception as e:
            console.print(f"\n[red]Browser error during Threads login: {e}[/red]")
            return False
        finally:
            context.close()

if __name__ == "__main__":
    login_threads()
