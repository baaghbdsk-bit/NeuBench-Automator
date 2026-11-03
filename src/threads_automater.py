"""

Autonomous Threads Browser Automater for NeuBench.

Uses Playwright with persistent session context to publish posts to Threads.

"""

import sys

import time
import re

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
        self.last_outcome_unknown = False
        self.last_message = ""



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

        self.last_outcome_unknown = False
        self.last_message = ""

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
                if "login" in page.url.lower():
                    return False, "Threads session expired or requires login."



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
                dialog = page.locator('div[role="dialog"]').first
                if dialog.count() > 0:
                    exact_btn = dialog.locator('div[role="button"], button').filter(has_text=re.compile(r"^Post$")).first
                    if exact_btn.count() > 0 and exact_btn.is_visible():
                        post_btn = exact_btn

                if not post_btn:
                    candidates = page.locator('div[role="button"], button').filter(has_text=re.compile(r"^Post$")).all()
                    for c in candidates:
                        if c.is_visible():
                            box = c.bounding_box()
                            if box and box['y'] > 300:
                                post_btn = c
                                break

                if not post_btn:
                    return False, "Could not locate 'Post' button on Threads."

                print("[ThreadsAutomater] Clicking 'Post' button...")
                post_btn.click(force=True)

                try:
                    page.wait_for_selector(
                        'text="Your thread was posted", text="Thread posted", [role="alert"]:has-text("posted")',
                        timeout=20000,
                    )
                except Exception:
                    self.last_outcome_unknown = True
                    self.last_message = "Threads submission was not confirmed; retry is blocked for this run."
                    return False, self.last_message

                print("[ThreadsAutomater] ✅ Successfully published post to Threads!")
                self.last_message = "Published to Threads successfully!"
                return True, self.last_message

            except Exception as e:

                self.last_message = f"Threads browser automation error: {e}"
                return False, self.last_message

            finally:

                context.close()



    def reply_to_viral_threads(self, query: str = "AI LLM", max_replies: int = 1) -> Tuple[int, str]:
        """
        Finds an active viral discussion on Threads and submits an insightful, professional reply.
        """
        if self.dry_run:
            print("[ThreadsAutomater] [DRY RUN] Simulated reply to Threads discussion.")
            return 0, "[DRY RUN] Simulated Threads reply"

        if not self.is_session_available():
            return 0, "Threads session not available for browser commenting."

        replied = 0
        with sync_playwright() as p:
            launch_kwargs = {
                "user_data_dir": str(self.user_data_dir),
                "headless": self.headless,
                "viewport": {"width": 1280, "height": 800},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
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
                            all_cookies = [{k: v for k, v in c.items() if k in ["name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite"]} for c in raw_cookies]
                            context.add_cookies(all_cookies)
                except Exception as e:
                    print(f"[ThreadsAutomater] Error restoring cookies: {e}")

            page = context.pages[0] if context.pages else context.new_page()
            try:
                from src.ai_generator import AIGenerator
                ai = AIGenerator()

                search_url = f"https://www.threads.net/search?q={query}&serp_type=default"
                print(f"[ThreadsAutomater] Navigating to {search_url} ...")
                page.goto(search_url, wait_until="domcontentloaded", timeout=40000)
                page.wait_for_timeout(4000)

                if "login" in page.url.lower():
                    return 0, "Threads session expired or requires login."

                # Locate the first high-engagement post container
                post_candidates = page.locator('div[data-pressable-container="true"], article').all()
                for post_card in post_candidates[:4]:
                    if replied >= max_replies:
                        break
                    try:
                        txt = post_card.inner_text().strip()
                        if len(txt) < 30 or "neubench" in txt.lower():
                            continue

                        # Look for Reply button (speech bubble icon or Reply text)
                        reply_trigger = post_card.locator('svg[aria-label="Reply"], button[aria-label="Reply"]').first
                        if not reply_trigger.is_visible():
                            continue

                        reply_trigger.click(timeout=3000)
                        page.wait_for_timeout(1500)

                        # Compose reply
                        editor = page.locator('div[role="textbox"][contenteditable="true"]').first
                        if editor.is_visible():
                            reply_text = ai.generate_sniper_reply(target_tweet_author="Threads User", target_tweet_text=txt[:300])
                            editor.click()
                            page.keyboard.insert_text(reply_text)
                            page.wait_for_timeout(1500)

                            post_btn = page.locator('div[role="button"]:has-text("Post"), button:has-text("Post")').last
                            if post_btn.is_visible():
                                post_btn.click(timeout=4000)
                                try:
                                    page.wait_for_selector(
                                        'text="Your reply was posted", text="Reply posted", [role="alert"]:has-text("posted")',
                                        timeout=15000,
                                    )
                                except Exception:
                                    continue
                                replied += 1
                                print("[ThreadsAutomater] ✅ Successfully replied on Threads!")
                    except Exception as ex:
                        print(f"[ThreadsAutomater] Error replying to item: {ex}")
                        continue

                return replied, f"Replied to {replied} Threads post(s)."
            except Exception as e:
                return replied, f"Threads reply error: {e}"
            finally:
                context.close()
