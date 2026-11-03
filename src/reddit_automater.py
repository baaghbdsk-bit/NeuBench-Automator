"""Reddit browser publisher using a saved Playwright session."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

from playwright.sync_api import sync_playwright

import config


class RedditAutomater:
    def __init__(self, headless: bool = True, dry_run: bool = False):
        self.headless = headless
        self.dry_run = dry_run
        self.user_data_dir = config.BASE_DIR / "reddit_session"
        self.last_outcome_unknown = False
        self.last_message = ""

    def is_session_available(self) -> bool:
        cookie_file = self.user_data_dir / "cookies.json"
        return cookie_file.exists() and cookie_file.stat().st_size > 20

    def _load_cookies(self):
        cookie_file = self.user_data_dir / "cookies.json"
        if not cookie_file.exists():
            return []
        try:
            data = json.loads(cookie_file.read_text(encoding="utf-8"))
            return data.get("cookies", data) if isinstance(data, dict) else data
        except Exception:
            return []

    def post(self, subreddit: str, title: str, body: str) -> Tuple[bool, str]:
        self.last_outcome_unknown = False
        self.last_message = ""
        if self.dry_run:
            self.last_message = f"[DRY RUN] Reddit post simulated for {subreddit}."
            return True, self.last_message
        if not self.is_session_available():
            self.last_message = "Reddit session is not authenticated. Run 'python main.py login-reddit'."
            return False, self.last_message
        if not title.strip() or not body.strip():
            self.last_message = "Reddit title and body are required."
            return False, self.last_message

        clean_subreddit = subreddit.strip().strip("/")
        if clean_subreddit.lower().startswith("r/"):
            clean_subreddit = clean_subreddit[2:]

        with sync_playwright() as p:
            context = None
            try:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    headless=self.headless,
                    viewport={"width": 1280, "height": 900},
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                )
                cookies = self._load_cookies()
                if cookies:
                    try:
                        context.add_cookies(cookies)
                    except Exception:
                        pass
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(
                    f"https://www.reddit.com/r/{clean_subreddit}/submit",
                    wait_until="domcontentloaded",
                    timeout=40000,
                )
                page.wait_for_timeout(3000)
                if "login" in page.url.lower():
                    self.last_message = "Reddit session expired or requires login."
                    return False, self.last_message

                title_input = page.locator('textarea[name="title"], input[name="title"], input[placeholder*="Title" i]').first
                title_input.wait_for(state="visible", timeout=15000)
                title_input.fill(title[:300])
                body_input = page.locator(
                    'textarea[name="text"], textarea[placeholder*="body" i], div[contenteditable="true"]'
                ).first
                body_input.wait_for(state="visible", timeout=15000)
                try:
                    body_input.fill(body)
                except Exception:
                    body_input.click()
                    page.keyboard.insert_text(body)

                submit = page.locator(
                    'button[type="submit"], button:has-text("Post"), button:has-text("Submit")'
                ).last
                submit.wait_for(state="visible", timeout=15000)
                submit.click(force=True)
                try:
                    page.wait_for_url("**/comments/**", timeout=30000)
                except Exception:
                    try:
                        page.wait_for_selector('[role="alert"]:has-text("submitted"), text="Post submitted"', timeout=10000)
                    except Exception:
                        self.last_outcome_unknown = True
                        self.last_message = "Reddit submission was not confirmed; retry blocked."
                        return False, self.last_message

                self.last_message = "Published to Reddit successfully."
                return True, self.last_message
            except Exception as error:
                self.last_message = f"Reddit browser error: {error}"
                return False, self.last_message
            finally:
                if context:
                    context.close()
