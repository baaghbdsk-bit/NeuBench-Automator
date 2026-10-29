import os
"""

Autonomous LinkedIn Browser Automater for NeuBench.

Uses Playwright with persistent session context to post high-value B2B updates.

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





class LinkedInAutomater:

    def __init__(self, headless: bool = True, dry_run: bool = False):

        self.headless = headless

        self.dry_run = dry_run

        self.user_data_dir = config.LINKEDIN_USER_DATA_DIR



    def is_session_available(self) -> bool:

        """Checks if a saved browser session directory exists with valid auth cookie."""

        if os.getenv("LINKEDIN_ACCESS_TOKEN") and os.getenv("LINKEDIN_PERSON_URN"):
            return True

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

            cur.execute("SELECT 1 FROM cookies WHERE name = 'li_at' LIMIT 1")

            has_cookie = cur.fetchone() is not None

            conn.close()

            return has_cookie

        except Exception:

            return self.user_data_dir.exists() and any(self.user_data_dir.iterdir())



    def post(self, text: str) -> Tuple[bool, str]:

        """Publishes an update to LinkedIn via automated browser session."""

        if self.dry_run:

            print(f"[LinkedInAutomater] [DRY RUN] Simulated LinkedIn post: {text[:60]}...")

            return True, f"[DRY RUN] Simulated post ({len(text)} chars)"



        # 1. Prefer Official LinkedIn REST API if access token is available
        access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        person_urn = os.getenv("LINKEDIN_PERSON_URN")
        if access_token and person_urn:
            print("[LinkedInAutomater] 🚀 Publishing via Official LinkedIn REST API...")
            try:
                import requests
                post_url = "https://api.linkedin.com/v2/ugcPosts"
                post_payload = {
                    "author": person_urn,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {
                                "text": text
                            },
                            "shareMediaCategory": "NONE"
                        }
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                    }
                }
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                    "Content-Type": "application/json"
                }
                resp = requests.post(post_url, json=post_payload, headers=headers, timeout=20)
                if resp.status_code in [200, 201]:
                    share_id = resp.json().get("id", "urn:li:share:published")
                    print(f"[LinkedInAutomater] ✅ Successfully published post to LinkedIn via Official API! ({share_id})")
                    return True, f"Published via Official LinkedIn API: {share_id}"
                else:
                    print(f"[LinkedInAutomater] API returned {resp.status_code}: {resp.text}. Falling back to browser...")
            except Exception as e:
                print(f"[LinkedInAutomater] API dispatch error: {e}. Falling back to browser...")

        if not self.is_session_available():

            return False, "LinkedIn session not authenticated. Run 'python main.py login-linkedin' to connect."



        with sync_playwright() as p:

            launch_kwargs = {
                "user_data_dir": str(self.user_data_dir),
                "headless": self.headless,
                "viewport": {"width": 1280, "height": 800},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
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
                            all_cookies = []
                            for c in raw_cookies:
                                # Ensure valid cookie fields and avoid duplicate conflicting domains
                                clean_c = {k: v for k, v in c.items() if k in ["name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite"]}
                                all_cookies.append(clean_c)
                            context.add_cookies(all_cookies)
                except Exception as e:
                    print(f"[LinkedInAutomater] Error restoring cookies: {e}")

            page = context.pages[0] if context.pages else context.new_page()



            try:

                print("[LinkedInAutomater] Navigating to https://www.linkedin.com/feed/ ...")

                page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=40000)

                page.wait_for_timeout(3500)



                # Check if logged in

                if "login" in page.url.lower() or "checkpoint" in page.url.lower():

                    return False, "Session expired or logged out. Please re-run 'python scripts/login_linkedin.py'."



                # Find the "Start a post" button

                post_trigger_selectors = [

                    'button[data-view-name="feed-share-box-trigger"]',

                    'button.share-box-feed-entry__trigger',

                    'button:has-text("Start a post")',

                    '.share-box-feed-entry__wrapper button',

                    'div[data-view-name="feed-share-box-trigger"] button'

                ]



                trigger_btn = page.get_by_text("Start a post", exact=True).first

                if not (trigger_btn and trigger_btn.is_visible()):

                    for sel in post_trigger_selectors:

                        btn = page.locator(sel).first

                        if btn.is_visible():

                            trigger_btn = btn

                            break



                if not trigger_btn:

                    return False, "Could not locate 'Start a post' button on LinkedIn feed."



                print("[LinkedInAutomater] Clicking 'Start a post' button...")

                trigger_btn.click()

                page.wait_for_timeout(4000)



                # Locate the post editor textbox

                editor_selectors = [

                    'div[role="textbox"][contenteditable="true"]',

                    'div.editor-content p',

                    'div.editor-content',

                    'div.ql-editor',

                    'div[aria-label*="editor" i]',

                    'div[aria-label*="share" i]'

                ]



                editor = None

                for _ in range(3):

                    for sel in editor_selectors:

                        ed = page.locator(sel).first

                        if ed.is_visible():

                            editor = ed

                            break

                    if editor:

                        break

                    page.wait_for_timeout(1500)



                if not editor:

                    return False, "Could not locate the post text editor modal on LinkedIn."



                print("[LinkedInAutomater] Entering post content into editor...")

                editor.click()

                page.wait_for_timeout(800)



                # Type content with natural feel

                # Using fill or clipboard paste to preserve formatting & linebreaks

                page.keyboard.insert_text(text)

                page.wait_for_timeout(1500)



                # Locate the "Post" button in modal

                post_btn_selectors = [

                    'button.share-actions__primary-action',

                    'button[data-view-name="share-post-button"]',

                    '.share-box_actions button:has-text("Post")',

                    'div[role="dialog"] button:has-text("Post")',

                    'button:has-text("Post")'

                ]



                post_btn = None
                for b in page.locator("button").all():
                    if b.is_visible() and b.inner_text().strip() == "Post":
                        post_btn = b
                        break

                if not post_btn:
                    for sel in post_btn_selectors:
                        btn = page.locator(sel).first
                        if btn.is_visible():
                            post_btn = btn
                            break

                if not post_btn:
                    return False, "Could not locate the 'Post' button in the post modal."

                print("[LinkedInAutomater] Clicking 'Post' button...")
                post_btn.click(force=True)
                page.wait_for_timeout(6000)



                print("[LinkedInAutomater] ✅ Successfully published post to LinkedIn!")

                return True, "Published to LinkedIn successfully!"



            except Exception as e:

                return False, f"LinkedIn browser automation error: {e}"

            finally:

                context.close()



