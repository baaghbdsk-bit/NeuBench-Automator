import sys
import time
import json
from pathlib import Path
from typing import Optional, Tuple
from playwright.sync_api import sync_playwright
import config

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

class PinterestAutomater:
    """Publishes vertical infographic pins to Pinterest (@neubench) with destination links."""

    def __init__(self, headless: bool = True, dry_run: bool = False):
        self.headless = headless
        self.dry_run = dry_run
        self.user_data_dir = config.BASE_DIR / "pinterest_session"
        self.last_outcome_unknown = False
        self.last_message = ""

    def is_session_available(self) -> bool:
        cookie_file = self.user_data_dir / "cookies.json"
        return cookie_file.exists()

    def create_pin(
        self,
        image_path: str,
        title: str,
        description: str,
        link: str = "https://neubench.netlify.app",
        board_name: Optional[str] = "Social"
    ) -> Tuple[bool, str]:
        """Uploads an image as a Pin on Pinterest with title, description, and website destination link."""
        self.last_outcome_unknown = False
        self.last_message = ""
        if self.dry_run:
            print(f"[PinterestAutomater] [DRY RUN] Would pin '{title}' to board '{board_name}' linking to {link}")
            return True, f"Simulated Pinterest Pin: {title}"

        if not self.is_session_available():
            return False, "Pinterest session not authenticated. Run 'python main.py login-pinterest'."

        img_file = Path(image_path).resolve()
        if not img_file.exists():
            return False, f"Image file not found: {image_path}"

        cookie_file = self.user_data_dir / "cookies.json"

        with sync_playwright() as p:
            args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars"
            ]
            browser = p.chromium.launch(headless=self.headless, args=args)
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )

            try:
                with open(cookie_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    if isinstance(cookies, list):
                        context.add_cookies(cookies)
            except Exception as e:
                print(f"[PinterestAutomater] Cookie restore warning: {e}")

            page = context.new_page()

            try:
                print("[PinterestAutomater] Navigating to Pinterest Pin creation studio...")
                page.goto("https://www.pinterest.com/pin-creation-tool/", wait_until="domcontentloaded", timeout=40000)
                page.wait_for_timeout(3500)

                # Check if redirected to login
                if "login" in page.url:
                    return False, "Pinterest session expired or invalid. Please re-run 'python main.py login-pinterest'."

                # 1. Upload Pin media
                print(f"[PinterestAutomater] Uploading pin image: {img_file.name}...")
                file_input = page.locator("input[type='file']").first
                file_input.wait_for(state="attached", timeout=15000)
                file_input.set_input_files(str(img_file))
                page.wait_for_timeout(3000)

                # 2. Enter Title
                print(f"[PinterestAutomater] Setting Pin title: {title[:40]}...")
                title_input = page.locator("#storyboard-selector-title, input[placeholder*='title' i], input[type='text']").first
                title_input.click()
                title_input.fill(title[:100])
                page.wait_for_timeout(1000)

                # 3. Enter Destination Link
                print(f"[PinterestAutomater] Setting destination link: {link}...")
                link_input = page.locator("#WebsiteField, input[placeholder*='link' i]").first
                link_input.click()
                link_input.fill(link)
                page.wait_for_timeout(1000)

                # 4. Select Board (Required to enable Publish button)
                print(f"[PinterestAutomater] Selecting Pinterest board: {board_name}...")
                board_btn = page.locator("[data-test-id='board-dropdown-select-button']").first
                if board_btn.is_visible(timeout=3000):
                    board_btn.click()
                    page.wait_for_timeout(1500)

                    board_row = page.locator(f"div[role='button']:has-text('{board_name}'), div:text-is('{board_name}')").last
                    if board_row.is_visible(timeout=2000):
                        board_row.click()
                    else:
                        page.locator("[role='option'], div[role='button']").last.click()
                    page.wait_for_timeout(1500)

                # 5. Publish Pin
                print("[PinterestAutomater] Clicking Publish button...")
                publish_btn = page.locator("[data-test-id='storyboard-creation-nav-done'] button, button:has-text('Publish')").first
                publish_btn.wait_for(state="visible", timeout=10000)

                for _ in range(20):
                    if not publish_btn.is_disabled():
                        break
                    page.wait_for_timeout(1000)

                publish_btn.click()
                try:
                    page.wait_for_selector(
                        '[data-test-id="toast"], [role="alert"]:has-text("published"), text="Your Pin is live"',
                        timeout=30000,
                    )
                except Exception:
                    self.last_outcome_unknown = True
                    self.last_message = "Pinterest submission was not confirmed; retry blocked."
                    return False, self.last_message

                print("[PinterestAutomater] ✅ Successfully published Pin to Pinterest!")
                self.last_message = "Published Pin to Pinterest"
                return True, self.last_message

            except Exception as e:
                print(f"[PinterestAutomater] ❌ Pin creation error: {e}")
                self.last_message = f"Pinterest error: {e}"
                return False, self.last_message
            finally:
                context.close()
                browser.close()
