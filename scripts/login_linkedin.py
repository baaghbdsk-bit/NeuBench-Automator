import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output on Windows
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

def login_linkedin():
    console.print("\n" + "="*60, style="bold blue")
    console.print("💼 LINKEDIN AUTONOMOUS BROWSER SESSION SETUP", style="bold white on blue")
    console.print("="*60, style="bold blue")
    console.print("\n[cyan]A visible Chrome/Chromium browser window will open now.[/cyan]")
    console.print("[yellow]1. Enter your LinkedIn email & password in the browser window.[/yellow]")
    console.print("[yellow]2. Complete any 2FA or verification prompt if asked.[/yellow]")
    console.print("[green]3. Once you reach your feed, this script will automatically detect it and save your session![/green]\n")

    user_data_dir = config.LINKEDIN_USER_DATA_DIR
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
            console.print("[dim]Navigating to https://www.linkedin.com/login ...[/dim]")
            page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=45000)

            console.print("[bold yellow]Waiting for you to log in... (Checking every 2 seconds)[/bold yellow]")

            # Loop waiting for feed or li_at cookie
            max_wait_seconds = 300  # 5 minutes
            start_wait = time.time()
            logged_in = False

            while time.time() - start_wait < max_wait_seconds:
                # 1. Check cookies for primary auth token
                try:
                    cookies = context.cookies()
                    if any(c.get("name") == "li_at" for c in cookies):
                        logged_in = True
                        break
                except Exception:
                    pass

                # 2. Check URL
                current_url = page.url.lower()
                if "feed" in current_url or "mynetwork" in current_url or "messaging" in current_url:
                    logged_in = True
                    break

                # 3. Check for global nav or profile icon
                try:
                    if page.locator('.global-nav__me-photo, img[alt*="photo"], [data-view-name="feed-share-box-trigger"]').first.is_visible():
                        logged_in = True
                        break
                except Exception:
                    pass

                time.sleep(2)

            if logged_in:
                console.print("\n[bold green]🎉 SUCCESS! Logged into LinkedIn successfully![/bold green]")
                console.print(f"[dim]Current URL: {page.url}[/dim]")
                time.sleep(3)
                console.print(f"[bold cyan]✅ Session saved securely into: {user_data_dir}[/bold cyan]")
                console.print("[green]The automater can now publish to LinkedIn 100% autonomously in the background![/green]\n")
                return True
            else:
                console.print("\n[red]Login timed out after 5 minutes. Please run this command again to retry.[/red]")
                return False

        except Exception as e:
            console.print(f"\n[red]Browser error during login: {e}[/red]")
            return False
        finally:
            context.close()

if __name__ == "__main__":
    login_linkedin()

