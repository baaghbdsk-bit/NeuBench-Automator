import sys
import time
from pathlib import Path
from rich.console import Console
from playwright.sync_api import sync_playwright
import config
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()

def login_instagram():
    """Interactive visual login tool for Instagram (@neubench) session persistence."""
    console.print("\n" + "="*60, style="bold magenta")
    console.print("📸 INSTAGRAM AUTONOMOUS SESSION SETUP (@neubench)", style="bold white on magenta")
    console.print("="*60, style="bold magenta")
    console.print("[yellow]1. A visible Chrome window will open to instagram.com/accounts/login[/yellow]")
    console.print("[yellow]2. Log in with your @neubench credentials.[/yellow]")
    console.print("[yellow]3. If prompted to 'Save Your Login Info', click 'Save Info' or 'Not Now'.[/yellow]")
    console.print("[green]4. Once you reach your Instagram home feed, return here and press ENTER.[/green]\n")

    user_data_dir = config.BASE_DIR / "instagram_session"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            console.print("[dim]Navigating to https://www.instagram.com/accounts/login/ ...[/dim]")
            page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=45000)

            input("\n👉 Press ENTER here in this console AFTER you are logged in and see your feed...\n")

            # Verify session cookies
            cookies = context.cookies()
            auth_cookies = [
                c for c in cookies
                if c.get("name") in ("sessionid", "ds_user_id") and "instagram.com" in c.get("domain", "")
            ]

            if not auth_cookies:
                console.print("[red]❌ Warning: No valid sessionid cookie detected for instagram.com.[/red]")
                console.print("[yellow]Make sure you completely logged in to your account.[/yellow]")
            else:
                cookie_file = user_data_dir / "cookies.json"
                with open(cookie_file, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, indent=2)
                console.print(f"[bold green]✅ Auth cookies saved to {cookie_file.relative_to(config.BASE_DIR)}![/bold green]")
                console.print(f"[bold green]🎉 SUCCESS! Instagram session for @neubench is ready.[/bold green]")

        except Exception as e:
            console.print(f"[red]Error during Instagram login setup: {e}[/red]")
        finally:
            context.close()

if __name__ == "__main__":
    login_instagram()
