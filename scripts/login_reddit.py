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

def login_reddit():
    console.print("\n" + "="*60, style="bold red")
    console.print("👽 REDDIT AUTONOMOUS BROWSER SESSION SETUP", style="bold white on red")
    console.print("="*60, style="bold red")
    console.print("\n[cyan]A visible Chrome/Chromium browser window will open now.[/cyan]")
    console.print("[yellow]1. Enter your Reddit username & password in the browser window.[/yellow]")
    console.print("[yellow]2. Complete any CAPTCHA or verification if requested.[/yellow]")
    console.print("[green]3. Once you log in, this script will automatically save your session![/green]\n")

    user_data_dir = config.BASE_DIR / "reddit_session"
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
            console.print("[dim]Navigating to https://www.reddit.com/login ...[/dim]")
            page.goto("https://www.reddit.com/login", wait_until="domcontentloaded", timeout=45000)

            console.print("[bold yellow]Waiting for you to log in... (Checking every 2 seconds)[/bold yellow]")

            max_wait_seconds = 300
            start_wait = time.time()
            logged_in = False
            account_username = ""

            while time.time() - start_wait < max_wait_seconds:
                # 1. Check cookies for session token
                try:
                    cookies = context.cookies()
                    if any(c.get("name") in ("reddit_session", "token") for c in cookies):
                        logged_in = True
                except Exception:
                    pass

                # 2. Check if navigated away from login
                current_url = page.url.lower()
                if "login" not in current_url and "register" not in current_url:
                    # Check for profile elements or username
                    try:
                        user_btn = page.locator('button[id*="USER_DROPDOWN"], #expand-user-drawer-button, [aria-label*="User menu"]').first
                        if user_btn and user_btn.is_visible():
                            logged_in = True
                            account_username = user_btn.inner_text().strip()
                            break
                    except Exception:
                        pass
                    if logged_in:
                        break

                time.sleep(2)

            if logged_in:
                console.print("\n[bold green]🎉 SUCCESS! Logged into Reddit successfully![/bold green]")
                if account_username:
                    console.print(f"[bold cyan]Connected Account: u/{account_username}[/bold cyan]")
                time.sleep(2)
                console.print(f"[bold cyan]✅ Session saved into: {user_data_dir}[/bold cyan]")
                return True
            else:
                console.print("\n[red]Login timed out after 5 minutes. Please try again.[/red]")
                return False

        except Exception as e:
            console.print(f"\n[red]Browser error during Reddit login: {e}[/red]")
            return False
        finally:
            context.close()

if __name__ == "__main__":
    login_reddit()
