import sys
import time
import json
from pathlib import Path
from typing import List, Tuple
from playwright.sync_api import sync_playwright
import config

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

class InstagramAutomater:
    """Automates publishing of 1080x1350 carousel image posts directly to Instagram (@neubench)."""

    def __init__(self, headless: bool = True, dry_run: bool = False):
        self.headless = headless
        self.dry_run = dry_run
        self.user_data_dir = config.BASE_DIR / "instagram_session"

    def is_session_available(self) -> bool:
        """Checks if a saved Instagram session with valid cookies exists."""
        cookie_file = self.user_data_dir / "cookies.json"
        if cookie_file.exists():
            return True
        return False

    def post_carousel(self, image_paths: List[str], caption: str) -> Tuple[bool, str]:
        """Publishes multi-slide carousel images to Instagram (@neubench)."""
        if self.dry_run:
            print(f"[InstagramAutomater] [DRY RUN] Would post {len(image_paths)} slides with caption: {caption[:60]}...")
            return True, f"Simulated Instagram carousel ({len(image_paths)} slides)"

        if not self.is_session_available():
            return False, "Instagram session not authenticated. Run 'python main.py login-instagram'."

        valid_images = [str(Path(p).resolve()) for p in image_paths if Path(p).exists()]
        if not valid_images:
            return False, "No valid image files provided for Instagram carousel."

        cookie_file = self.user_data_dir / "cookies.json"

        with sync_playwright() as p:
            args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars"
            ]
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.headless,
                viewport={"width": 1280, "height": 900},
                args=args,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )

            # Restore cookies if present
            if cookie_file.exists():
                try:
                    with open(cookie_file, "r", encoding="utf-8") as f:
                        c_data = json.load(f)
                        raw_cookies = c_data.get("cookies", c_data) if isinstance(c_data, dict) else c_data
                        if isinstance(raw_cookies, list):
                            context.add_cookies(raw_cookies)
                except Exception as e:
                    print(f"[InstagramAutomater] Cookie restore note: {e}")

            page = context.pages[0] if context.pages else context.new_page()

            try:
                print("[InstagramAutomater] Navigating to https://www.instagram.com/ ...")
                page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=40000)
                page.wait_for_timeout(3000)

                # Dismiss 'Turn on Notifications' or cookies popups if present
                for dismiss_text in ["Not Now", "Cancel", "Decline optional cookies"]:
                    try:
                        btn = page.locator(f'button:has-text("{dismiss_text}")')
                        if btn.is_visible(timeout=1500):
                            btn.click()
                            page.wait_for_timeout(1000)
                    except Exception:
                        pass

                # Locate the 'New post' / 'Create' button (SVG or aria-label)
                create_btn = page.locator('svg[aria-label="New post"], svg[aria-label="Create"], [aria-label="New post"]').first
                if not create_btn.is_visible(timeout=10000):
                    # Check if 'Create' text exists in side nav
                    create_btn = page.locator('span:has-text("Create"), a:has-text("Create")').first

                print("[InstagramAutomater] Clicking Create post button...")
                create_btn.click()
                page.wait_for_timeout(2500)

                # File input handler for multi-image upload
                file_input = page.locator('input[type="file"]').first
                file_input.set_input_files(valid_images)
                page.wait_for_timeout(3000)

                # Set aspect ratio to Original / 4:5 if selector exists
                try:
                    ratio_btn = page.locator('svg[aria-label="Select crop"], button:has-text("Select crop")').first
                    if ratio_btn.is_visible(timeout=2000):
                        ratio_btn.click()
                        page.wait_for_timeout(500)
                        orig_btn = page.locator('span:has-text("Original"), span:has-text("4:5")').first
                        if orig_btn.is_visible(timeout=1500):
                            orig_btn.click()
                            page.wait_for_timeout(500)
                except Exception:
                    pass

                # Click 'Next' button (Top right of modal)
                next_btn = page.locator('div[role="dialog"] div:has-text("Next"), button:has-text("Next")').last
                next_btn.click()
                page.wait_for_timeout(2000)

                # Second 'Next' button (Filter step)
                next_btn2 = page.locator('div[role="dialog"] div:has-text("Next"), button:has-text("Next")').last
                next_btn2.click()
                page.wait_for_timeout(2000)

                # Type caption in the textarea / contenteditable div
                caption_area = page.locator('div[role="dialog"] div[aria-label="Write a caption..."], div[role="textbox"]').first
                caption_area.click()
                page.wait_for_timeout(500)
                caption_area.fill(caption)
                page.wait_for_timeout(1500)

                # Click 'Share' button
                share_btn = page.locator('div[role="dialog"] div:has-text("Share"), button:has-text("Share")').last
                print("[InstagramAutomater] Clicking Share button...")
                share_btn.click()

                # Wait for confirmation: 'Your post has been shared.'
                page.wait_for_selector('text="Your post has been shared."', timeout=35000)
                print("[InstagramAutomater] ✅ Successfully published carousel to Instagram (@neubench)!")
                return True, "Published carousel to Instagram (@neubench)"

            except Exception as e:
                print(f"[InstagramAutomater] ❌ Publish failed: {e}")
                return False, f"Instagram publish error: {e}"
            finally:
                context.close()
