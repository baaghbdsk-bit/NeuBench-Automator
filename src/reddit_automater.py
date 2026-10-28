"""

Autonomous Reddit Browser Automater for NeuBench.

Uses Playwright with persistent session context to submit posts to target subreddits.

Reddit blocks headless automation, so runs headed.

"""

import sys

import time

import random

from pathlib import Path

from typing import Tuple



from playwright.sync_api import sync_playwright

import config



if sys.platform == "win32":

    try:

        sys.stdout.reconfigure(encoding="utf-8")

        sys.stderr.reconfigure(encoding="utf-8")

    except Exception:

        pass





class RedditAutomater:

    def __init__(self, headless: bool = True, dry_run: bool = False):

        self.headless = headless

        self.dry_run = dry_run

        self.user_data_dir = config.BASE_DIR / "reddit_session"



    def is_session_available(self) -> bool:
        if (self.user_data_dir / "cookies.json").exists():
            return True

        cookie_db = self.user_data_dir / "Default" / "Network" / "Cookies"

        if not cookie_db.exists():

            return self.user_data_dir.exists() and any(self.user_data_dir.iterdir())

        try:

            import sqlite3

            uri = f"file:{cookie_db.resolve().as_posix()}?mode=ro"

            conn = sqlite3.connect(uri, uri=True)

            cur = conn.cursor()

            cur.execute("SELECT 1 FROM cookies WHERE name IN ('reddit_session','token_v2') LIMIT 1")

            has = cur.fetchone() is not None

            conn.close()

            return has

        except Exception:

            return self.user_data_dir.exists() and any(self.user_data_dir.iterdir())



    def post(self, subreddit: str, title: str, body: str) -> Tuple[bool, str]:

        if self.dry_run:

            print(f"[RedditAutomater] [DRY RUN] Simulated Reddit post to {subreddit}: {title[:60]}...")

            return True, f"[DRY RUN] Simulated post ({len(body)} chars)"



        if not self.is_session_available():

            return False, "Reddit session not authenticated. Run 'python main.py login-reddit'."



        sub = subreddit.replace("r/", "").strip()

        url = f"https://www.reddit.com/r/{sub}/submit?type=TEXT"



        with sync_playwright() as p:

            launch_kwargs = {

                "user_data_dir": str(self.user_data_dir),

                "headless": self.headless,

                "viewport": {"width": 1280, "height": 900},

                "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox", "--window-position=-2400,-2400"]

            }

            try:

                context = p.chromium.launch_persistent_context(**launch_kwargs, channel="chrome")

            except Exception:

                context = p.chromium.launch_persistent_context(**launch_kwargs)

            cookie_file = self.user_data_dir / "cookies.json"
            if cookie_file.exists():
                try:
                    import json
                    with open(cookie_file, "r", encoding="utf-8") as f:
                        c_data = json.load(f)
                        raw_cookies = c_data.get("cookies", c_data) if isinstance(c_data, dict) else c_data
                        if isinstance(raw_cookies, list):
                            context.add_cookies(raw_cookies)
                except Exception as e:
                    print(f"[RedditAutomater] Error restoring cookies: {e}")

            page = context.pages[0] if context.pages else context.new_page()



            try:

                print(f"[RedditAutomater] Navigating to {url} ...")

                page.goto(url, wait_until="domcontentloaded", timeout=45000)

                page.wait_for_timeout(6000)



                if "login" in page.url.lower():

                    return False, "Reddit session expired. Re-run 'python main.py login-reddit'."



                title_filled = False
                for sel in [
                    'textarea[name="title"]',
                    'textarea[placeholder*="Title"]',
                    'input[placeholder*="Title"]',
                    'input[name="title"]',
                    '[data-testid="post-title-input"]',
                    'faceplate-textarea-input textarea',
                    'shreddit-composer [name="title"]'
                ]:
                    try:
                        el = page.locator(sel).first
                        if el.is_visible():
                            el.fill(title)
                            title_filled = True
                            break
                    except Exception:
                        pass

                if not title_filled:
                    try:
                        page.wait_for_selector('textarea[name="title"], textarea[placeholder*="Title"], input[placeholder*="Title"]', timeout=10000)
                        title_el = page.locator('textarea[name="title"], textarea[placeholder*="Title"], input[placeholder*="Title"]').first
                        title_el.fill(title)
                        title_filled = True
                    except Exception:
                        pass

                if not title_filled:
                    return False, "Could not locate title field on Reddit submit page."

                page.wait_for_timeout(500)



                # Switch to Markdown mode so formatting (**bold**, bullets, links) renders natively without literal asterisks

                page.evaluate('''() => {

                    const btn = document.querySelector('button[aria-label="Switch to Markdown"]') || 

                                Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Switch to Markdown'));

                    if (btn) btn.click();

                }''')

                page.wait_for_timeout(1000)



                body_textarea = page.locator('textarea[placeholder*="Body text"], textarea[name="body"]').first

                if body_textarea.is_visible():

                    body_textarea.fill(body)

                    page.wait_for_timeout(500)

                else:

                    body_el = page.locator('div[name="body"]').first

                    if body_el.is_visible():

                        body_el.click()

                        page.wait_for_timeout(500)

                        clean_body = body.replace("**", "")

                        page.keyboard.insert_text(clean_body)

                        page.wait_for_timeout(1000)



                post_btn = page.get_by_role("button", name="Post").first

                if not post_btn.is_visible():

                    # fallback

                    for b in page.locator("button").all():

                        if b.is_visible() and b.inner_text().strip() == "Post":

                            post_btn = b

                            break

                if not post_btn.is_visible():

                    return False, "Could not locate 'Post' button on Reddit."



                print("[RedditAutomater] Clicking 'Post' button...")
                try:
                    post_btn.click(force=True, timeout=10000)
                except Exception:
                    post_btn.dispatch_event("click")

                page.wait_for_timeout(6000)

                print("[RedditAutomater] ✅ Submitted post to Reddit!")

                return True, f"Published to r/{sub} successfully!"

            except Exception as e:

                return False, f"Reddit browser automation error: {e}"

            finally:

                context.close()

