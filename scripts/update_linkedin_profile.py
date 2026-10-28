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

def update_linkedin_profile(
    first_name: str = "NeuBench",
    last_name: str = "AI",
    headline: str = "Building NeuBench • Real-Time AI Benchmarks across 266+ Models | LLM Evals & Engineering Commentary",
    banner_path: str = "assets/neubench_linkedin_banner.jpg",
    avatar_path: str = "assets/neubench_avatar.jpg"
):
    console.print("\n" + "="*60, style="bold blue")
    console.print("💼 UPDATING LINKEDIN PROFILE TO NEUBENCH", style="bold white on blue")
    console.print("="*60, style="bold blue")
    console.print(f"  First Name: {first_name}")
    console.print(f"  Last Name:  {last_name}")
    console.print(f"  Headline:   {headline}")
    if banner_path: console.print(f"  Banner:     {banner_path}")
    if avatar_path: console.print(f"  Avatar:     {avatar_path}\n")

    user_data_dir = config.LINKEDIN_USER_DATA_DIR

    with sync_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(user_data_dir),
            "headless": True,
            "viewport": {"width": 1280, "height": 850},
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        }
        try:
            ctx = p.chromium.launch_persistent_context(**launch_kwargs, channel="chrome")
        except Exception:
            ctx = p.chromium.launch_persistent_context(**launch_kwargs)

        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            console.print("[dim]Navigating to your LinkedIn profile...[/dim]")
            page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(3500)

            console.print(f"[dim]Profile URL: {page.url}[/dim]")

            # 1. Update Banner if provided
            if banner_path and Path(banner_path).exists():
                console.print(f"[cyan]Uploading background banner: {banner_path}...[/cyan]")
                try:
                    # Look for banner edit button
                    banner_btn = page.locator('button[aria-label*="Edit background"], button[aria-label*="banner"], button[aria-label*="background photo"], .profile-background-image button').first
                    if banner_btn and banner_btn.is_visible():
                        banner_btn.click()
                        page.wait_for_timeout(2000)

                    file_input = page.locator('input[type="file"]').first
                    if file_input:
                        file_input.set_input_files(str(Path(banner_path).resolve()))
                        page.wait_for_timeout(3000)
                        
                        # Click Apply / Save button
                        apply_btn = page.locator('button:has-text("Apply"), button:has-text("Save"), button.artdeco-button--primary').first
                        if apply_btn and apply_btn.is_visible():
                            apply_btn.click()
                            page.wait_for_timeout(3000)
                            console.print("[bold green]✅ Background banner uploaded and applied![/bold green]")
                except Exception as e_banner:
                    console.print(f"[yellow]Note on banner upload: {e_banner}[/yellow]")

            # 2. Click "Edit intro" (pencil icon on top card)
            console.print("[cyan]Opening 'Edit intro' form...[/cyan]")
            edit_btn = page.locator('button[aria-label*="Edit intro"], button[aria-label*="edit intro"], a[href*="edit-intro"], svg[data-test-icon*="edit-small"] button, .pv-top-card--list button').first
            
            # Alternative: find pen icon in main profile section
            if not (edit_btn and edit_btn.is_visible()):
                edit_btn = page.locator('main section button:has(svg)').first

            if edit_btn:
                edit_btn.click()
                page.wait_for_timeout(3000)
            else:
                # Direct navigation to edit-intro overlay
                profile_slug = page.url.rstrip('/').split('/')[-1]
                page.goto(f"https://www.linkedin.com/in/{profile_slug}/overlay/edit-intro/", timeout=30000)
                page.wait_for_timeout(3000)

            # Look for input fields in the modal
            # First Name
            fn_input = page.locator('input[id*="first-name"], input[name*="firstName"], input[id*="single-line-text-form-component-profileEditFormElement-TOP-CARD-profile"]').first
            if fn_input and fn_input.is_visible():
                console.print(f"[cyan]Setting First Name to: {first_name}[/cyan]")
                fn_input.fill("")
                fn_input.fill(first_name)
            else:
                # Try finding by label
                page.get_by_label("First name").first.fill(first_name)

            # Last Name
            try:
                page.get_by_label("Last name").first.fill(last_name)
                console.print(f"[cyan]Setting Last Name to: {last_name}[/cyan]")
            except Exception:
                pass

            # Headline
            try:
                hl_input = page.get_by_label("Headline").first
                if hl_input and hl_input.is_visible():
                    console.print(f"[cyan]Setting Headline to: {headline}[/cyan]")
                    hl_input.fill("")
                    hl_input.fill(headline)
            except Exception:
                # Try textarea
                hl_ta = page.locator('textarea[id*="headline"], textarea[name*="headline"]').first
                if hl_ta and hl_ta.is_visible():
                    hl_ta.fill("")
                    hl_ta.fill(headline)

            page.wait_for_timeout(1500)

            # Save intro form
            console.print("[cyan]Saving updated profile details...[/cyan]")
            save_btn = page.locator('button:has-text("Save"), button.artdeco-button--primary').last
            if save_btn and save_btn.is_visible():
                save_btn.click()
                page.wait_for_timeout(4000)
                console.print("[bold green]🎉 SUCCESS! LinkedIn profile updated to NeuBench![/bold green]")
            else:
                console.print("[yellow]Could not find Save button in intro modal.[/yellow]")

            # Update cached profile JSON
            profile_data = {
                "name": f"{first_name} {last_name}".strip(),
                "headline": headline,
                "location": "Kakori, Uttar Pradesh, India",
                "profile_url": page.url,
                "connections": 7,
                "followers": 7,
                "impressions": 0,
                "profile_views": 0,
                "search_appearances": 0
            }
            with open(config.BASE_DIR / "linkedin_profile.json", "w", encoding="utf-8") as f:
                import json
                json.dump(profile_data, f, indent=2)

            return True

        except Exception as e:
            console.print(f"[red]Error updating LinkedIn profile: {e}[/red]")
            return False
        finally:
            ctx.close()

if __name__ == "__main__":
    update_linkedin_profile()

