"""

Autonomous Threads Browser Automater for NeuBench.

Uses Playwright with persistent session context to publish posts to Threads.

"""

import sys

import time

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





class ThreadsAutomater:

    def __init__(self, headless: bool = True, dry_run: bool = False):

        self.headless = headless

        self.dry_run = dry_run

        self.user_data_dir = config.BASE_DIR / "threads_session"



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

            cur.execute("SELECT 1 FROM cookies WHERE name IN ('sessionid','csrftoken','ds_user_id') LIMIT 1")

            has = cur.fetchone() is not None

            conn.close()

            return has

        except Exception:

            return self.user_data_dir.exists() and any(self.user_data_dir.iterdir())



    def post(self, text: str) -> Tuple[bool, str]:

        if self.dry_run:

            print(f"[ThreadsAutomater] [DRY RUN] Simulated Threads post: {text[:60]}...")

            return True, f"[DRY RUN] Simulated post ({len(text)} chars)"



        if not self.is_session_available():

            return False, "Threads session not authenticated. Run 'python main.py login-threads'."



        with sync_playwright() as p:

            launch_kwargs = {

                "user_data_dir": str(self.user_data_dir),

                "headless": self.headless,

                "viewport": {"width": 1280, "height": 800},

                "args": ["--disable-blink-features=AutomationControlled", "--no-sandbox"]

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
                    print(f"[ThreadsAutomater] Error restoring cookies: {e}")

            page = context.pages[0] if context.pages else context.new_page()



            try:

                print("[ThreadsAutomater] Navigating to https://www.threads.net/ ...")

                page.goto("https://www.threads.net/", wait_until="domcontentloaded", timeout=40000)

                page.wait_for_timeout(6000)



                # Open composer

                trigger = page.get_by_text("What’s new?", exact=False).first

                if not trigger.is_visible():

                    return False, "Could not locate Threads composer trigger."

                clickable = trigger.evaluate_handle("""el => {

                    let cur = el;

                    while (cur && cur !== document.body) {

                        const role = cur.getAttribute && cur.getAttribute('role');

                        if (role === 'button' || cur.tagName === 'BUTTON' || cur.getAttribute('tabindex') === '0') return cur;

                        cur = cur.parentElement;

                    }

                    return el;

                }""")

                clickable.click()

                page.wait_for_timeout(2500)



                editor = page.locator('div[contenteditable="true"]').first

                if not editor.is_visible():

                    return False, "Could not locate Threads text editor."

                editor.click()

                page.wait_for_timeout(500)

                page.keyboard.insert_text(text)

                page.wait_for_timeout(1500)



                post_btn = None

                candidates = page.get_by_text("Post", exact=True)

                for i in range(candidates.count()):

                    c = candidates.nth(i)

                    if c.is_visible():

                        box = c.bounding_box()

                        if box and box['y'] > 200:  # Select composer submit button, not top navigation

                            post_btn = c

                            break

                if not post_btn:

                    # fallback to any visible candidate

                    for i in range(candidates.count()):

                        c = candidates.nth(i)

                        if c.is_visible():

                            post_btn = c

                            break



                if not post_btn:

                    return False, "Could not locate 'Post' button on Threads."



                print("[ThreadsAutomater] Clicking 'Post' button...")

                post_btn.click(force=True)

                page.wait_for_timeout(7000)

                print("[ThreadsAutomater] ✅ Successfully published post to Threads!")

                return True, "Published to Threads successfully!"

            except Exception as e:

                return False, f"Threads browser automation error: {e}"

            finally:

                context.close()

