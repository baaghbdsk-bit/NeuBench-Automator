"""Autonomous LinkedIn Browser Automater: posting, media upload, and viral engagement."""
import hashlib
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

ACHIEVEMENT_KEYWORDS = (
    "congratulations", "congrats", "promoted", "promotion", "new role",
    "new chapter", "new journey", "excited to announce", "excited to share",
    "happy to share", "proud to share", "proud to announce", "joined",
    "graduated", "graduation", "certification", "certified", "award",
    "funding", "raised", "milestone", "hired", "new job", "first day",
    "work anniversary", "speaker", "launched", "launching",
)

SUITABILITY_BLOCKLIST = (
    "election", "political", "politics", "religion", "nsfw", "gambling",
    "crypto scam", "adult content",
)



from playwright.sync_api import sync_playwright

import config

from src.linkedin_state import engagement_key



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

        # Set when a submission may have been accepted but its final response
        # could not be observed. Callers must not blindly retry that attempt.
        self.last_post_outcome_unknown = False



    def is_session_available(self) -> bool:

        """Checks if a saved browser session directory exists with valid auth cookie."""

        if os.getenv("LINKEDIN_ACCESS_TOKEN") and os.getenv("LINKEDIN_PERSON_URN"):
            return True

        return self.is_browser_session_available()


    def is_browser_session_available(self) -> bool:
        """Check browser credentials separately from REST API credentials."""

        cookie_file = self.user_data_dir / "cookies.json"
        if cookie_file.exists():
            try:
                with cookie_file.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                raw_cookies = data.get("cookies", data) if isinstance(data, dict) else data
                if isinstance(raw_cookies, list):
                    return any(
                        item.get("name") == "li_at" and item.get("value")
                        for item in raw_cookies
                        if isinstance(item, dict)
                    )
            except (OSError, TypeError, ValueError):
                return False

        cookie_db = self.user_data_dir / "Default" / "Network" / "Cookies"

        if not cookie_db.exists():
            return False

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

            return False



    def _api_headers(self, include_content_type: bool = True) -> Dict[str, str]:

        headers = {
            "Authorization": f"Bearer {os.getenv('LINKEDIN_ACCESS_TOKEN', '').strip()}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Linkedin-Version": config.LINKEDIN_API_VERSION,
        }
        if include_content_type:
            headers["Content-Type"] = "application/json"
        return headers


    def _wait_for_media_available(self, media_urn: str, media_kind: str, max_seconds: int = 60) -> bool:
        """Polls LinkedIn REST API until uploaded image/video achieves AVAILABLE status."""
        import urllib.parse
        encoded_urn = urllib.parse.quote(media_urn, safe="")
        endpoint = f"https://api.linkedin.com/rest/{'videos' if media_kind == 'video' else 'images'}/{encoded_urn}"
        headers = self._api_headers(include_content_type=False)
        start = time.time()
        while time.time() - start < max_seconds:
            try:
                res = requests.get(endpoint, headers=headers, timeout=15)
                if res.status_code == 200:
                    status = res.json().get("status")
                    if status == "AVAILABLE":
                        return True
                    if status in ("CLIENT_ERROR", "PROCESSING_FAILED"):
                        print(f"[LinkedInAutomater] Media processing failed: {res.text[:200]}")
                        return False
            except Exception as e:
                print(f"[LinkedInAutomater] Media status poll notice: {e}")
            time.sleep(2.5)
        print(f"[LinkedInAutomater] Media did not reach AVAILABLE status within {max_seconds}s.")
        return False

    def _upload_video(self, image_path: str, person_urn: str) -> str:

        """Uploads an MP4 through LinkedIn's current versioned Videos API."""

        file_size = os.path.getsize(image_path)
        init_res = requests.post(
            "https://api.linkedin.com/rest/videos?action=initializeUpload",
            headers=self._api_headers(),
            json={
                "initializeUploadRequest": {
                    "owner": person_urn,
                    "fileSizeBytes": file_size,
                    "uploadCaptions": False,
                    "uploadThumbnail": False,
                }
            },
            timeout=30,
        )
        if init_res.status_code not in (200, 201):
            raise RuntimeError(f"video initialize returned {init_res.status_code}: {init_res.text[:300]}")

        value = init_res.json().get("value", {})
        video_urn = value.get("video")
        instructions = value.get("uploadInstructions") or []
        upload_token = value.get("uploadToken", "")
        if not video_urn or not instructions:
            raise RuntimeError("video initialize response did not include an upload target")

        uploaded_part_ids = []
        with open(image_path, "rb") as media_file:
            for instruction in instructions:
                first_byte = int(instruction["firstByte"])
                last_byte = int(instruction["lastByte"])
                media_file.seek(first_byte)
                part = media_file.read(last_byte - first_byte + 1)
                upload_res = requests.put(
                    instruction["uploadUrl"],
                    headers={
                        "Content-Type": "application/octet-stream",
                        "Content-Range": f"bytes {first_byte}-{last_byte}/{file_size}",
                    },
                    data=part,
                    timeout=120,
                )
                if upload_res.status_code not in (200, 201, 204):
                    raise RuntimeError(f"video part upload returned {upload_res.status_code}: {upload_res.text[:300]}")
                etag = upload_res.headers.get("ETag") or upload_res.headers.get("etag")
                if not etag:
                    raise RuntimeError("video part upload did not return an ETag")
                uploaded_part_ids.append(etag.strip('"'))

        finalize_res = requests.post(
            "https://api.linkedin.com/rest/videos?action=finalizeUpload",
            headers=self._api_headers(),
            json={
                "finalizeUploadRequest": {
                    "video": video_urn,
                    "uploadToken": upload_token,
                    "uploadedPartIds": uploaded_part_ids,
                }
            },
            timeout=30,
        )
        if finalize_res.status_code not in (200, 201):
            raise RuntimeError(f"video finalize returned {finalize_res.status_code}: {finalize_res.text[:300]}")
        return video_urn


    def _upload_image(self, image_path: str, person_urn: str) -> str:
        """Uploads a PNG/JPG/GIF through LinkedIn's versioned Images API."""
        ext = os.path.splitext(image_path)[1].lower()
        content_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
        }.get(ext, "application/octet-stream")

        init_res = requests.post(
            "https://api.linkedin.com/rest/images?action=initializeUpload",
            headers=self._api_headers(),
            json={"initializeUploadRequest": {"owner": person_urn}},
            timeout=30,
        )
        if init_res.status_code not in (200, 201):
            raise RuntimeError(f"image initialize returned {init_res.status_code}: {init_res.text[:300]}")

        value = init_res.json().get("value", {})
        upload_url = value.get("uploadUrl")
        image_urn = value.get("image")
        if not upload_url or not image_urn:
            raise RuntimeError("image initialize response did not include an upload target")

        with open(image_path, "rb") as media_file:
            upload_res = requests.put(
                upload_url,
                headers={"Content-Type": content_type},
                data=media_file,
                timeout=120,
            )
        if upload_res.status_code not in (200, 201, 204):
            raise RuntimeError(f"image upload returned {upload_res.status_code}: {upload_res.text[:300]}")
        return image_urn


    def add_comment_to_post(self, post_urn: str, comment_text: str) -> Tuple[bool, str]:
        """
        Adds a first comment (takeaway, code snippet, or interactive question)
        to a published LinkedIn post via Official REST API or browser session.
        """
        if self.dry_run:
            print(f"[LinkedInAutomater] [DRY RUN] Would comment on {post_urn}: {comment_text[:60]}...")
            return True, "[DRY RUN] Comment simulated"

        access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        person_urn = os.getenv("LINKEDIN_PERSON_URN")
        if access_token and person_urn:
            try:
                import urllib.parse
                encoded_parent = urllib.parse.quote(post_urn)
                comment_url = f"https://api.linkedin.com/rest/socialActions/{encoded_parent}/comments"
                headers = self._api_headers()
                payload = {
                    "actor": person_urn,
                    "object": post_urn,
                    "message": {"text": comment_text}
                }
                res = requests.post(comment_url, headers=headers, json=payload, timeout=15)
                if res.status_code in (200, 201):
                    c_id = res.json().get("id", "comment_created")
                    print(f"[LinkedInAutomater] 💬 First-comment successfully added to post! ({c_id})")
                    return True, f"Comment added: {c_id}"
                else:
                    print(f"[LinkedInAutomater] Comment API error: {res.status_code} - {res.text}")
            except Exception as e:
                print(f"[LinkedInAutomater] Failed to add comment via API: {e}")
        return False, "Could not add comment via API"

    def post(self, text: str, image_path: Optional[str] = None, first_comment: Optional[str] = None) -> Tuple[bool, str]:

        """Publishes an update to LinkedIn via automated browser session."""

        self.last_post_outcome_unknown = False

        if self.dry_run:
            print(f"[LinkedInAutomater] [DRY RUN] Simulated LinkedIn post: {text[:60]}...")
            if first_comment:
                print(f"[LinkedInAutomater] [DRY RUN] Simulated first comment: {first_comment[:60]}...")
            return True, f"[DRY RUN] Simulated post ({len(text)} chars)"



        # 1. Prefer Official LinkedIn REST API if access token is available
        access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        person_urn = os.getenv("LINKEDIN_PERSON_URN")
        if access_token and person_urn:
            print("[LinkedInAutomater] 🚀 Publishing via Official LinkedIn REST API...")
            media_urn = None
            media_kind = None
            media_title = "NeuBench Technical Visual"
            if image_path and os.path.exists(image_path):
                ext = os.path.splitext(image_path)[1].lower()
                try:
                    if ext == ".mp4":
                        media_urn = self._upload_video(image_path, person_urn)
                        media_kind = "video"
                    else:
                        media_urn = self._upload_image(image_path, person_urn)
                        media_kind = "image"
                except Exception as media_error:
                    print(f"[LinkedInAutomater] Media upload note: {media_error}. Trying fallback...")
                    if ext == ".mp4":
                        try:
                            gif_sibling = os.path.splitext(image_path)[0] + ".gif"
                            if os.path.exists(gif_sibling):
                                media_urn = self._upload_image(gif_sibling, person_urn)
                                media_kind = "image"
                        except Exception as gif_error:
                            print(f"[LinkedInAutomater] Video-to-GIF fallback skipped: {gif_error}")
                    elif ext == ".gif":
                        try:
                            from PIL import Image
                            still_path = os.path.splitext(image_path)[0] + "_still.png"
                            with Image.open(image_path) as frame:
                                frame.convert("RGB").save(still_path)
                            media_urn = self._upload_image(still_path, person_urn)
                            media_kind = "image"
                        except Exception as still_error:
                            print(f"[LinkedInAutomater] GIF still-frame fallback skipped: {still_error}")

                if media_urn and media_kind:
                    print(f"[LinkedInAutomater] ⏳ Verifying LinkedIn {media_kind} availability ({media_urn})...")
                    is_ready = self._wait_for_media_available(media_urn, media_kind, max_seconds=45)
                    if not is_ready:
                        print(f"[LinkedInAutomater] ⚠️ Media {media_urn} not ready in time. Posting text-only to ensure delivery.")
                        media_urn = None
                        media_kind = None

            post_payload = {
                "author": person_urn,
                "commentary": text,
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": []
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False
            }
            if media_urn:
                if media_kind == "video":
                    media_obj = {"id": media_urn, "title": media_title}
                else:
                    media_obj = {"id": media_urn, "altText": media_title}
                post_payload["content"] = {"media": media_obj}

            post_url = "https://api.linkedin.com/rest/posts"
            headers = self._api_headers()
            try:
                resp = requests.post(post_url, json=post_payload, headers=headers, timeout=20)
            except Exception as e:
                self.last_post_outcome_unknown = True
                msg = f"LinkedIn API outcome unknown ({e}); skipped browser fallback to avoid a duplicate post."
                print(f"[LinkedInAutomater] {msg}")
                return False, msg

            if resp.status_code in [200, 201]:
                share_id = resp.headers.get("X-RestLi-Id") or resp.headers.get("x-restli-id")
                if not share_id:
                    try:
                        share_id = resp.json().get("id")
                    except ValueError:
                        share_id = None
                share_id = share_id or "published"
                print(f"[LinkedInAutomater] ✅ Successfully published post to LinkedIn via Official API! ({share_id})")
                if first_comment:
                    try:
                        self.add_comment_to_post(share_id, first_comment)
                    except Exception as ce:
                        print(f"[LinkedInAutomater] Note on first-comment: {ce}")
                return True, f"Published via Official LinkedIn API: {share_id}"

            if resp.status_code in (401, 403):
                print(f"[LinkedInAutomater] API auth error {resp.status_code}. Falling back to browser...")
            else:
                msg = f"LinkedIn API returned {resp.status_code}: {resp.text[:300]}"
                print(f"[LinkedInAutomater] {msg}")
                return False, msg

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

            submission_started = False


            try:

                print("[LinkedInAutomater] Navigating to https://www.linkedin.com/feed/ ...")

                page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=40000)

                page.wait_for_timeout(3500)



                # Check if logged in

                if any(marker in page.url.lower() for marker in ("login", "checkpoint", "challenge", "authwall")):

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

                # Attach media if available
                if image_path and os.path.exists(image_path):
                    try:
                        print(f"[LinkedInAutomater] Attaching media to LinkedIn post via browser: {image_path}...")
                        resolved_media = str(Path(image_path).resolve())
                        file_input = page.locator('input[type="file"]').first
                        if file_input.count():
                            file_input.set_input_files(resolved_media)
                            page.wait_for_timeout(4000)
                            next_btn = page.locator('button:has-text("Next"), button.share-box-footer__primary-btn, button[aria-label*="Next" i]').first
                            if next_btn.is_visible():
                                print("[LinkedInAutomater] Clicking 'Next' in media modal...")
                                next_btn.click()
                                page.wait_for_timeout(3000)
                    except Exception as media_err:
                        print(f"[LinkedInAutomater] Browser media attach note: {media_err}")



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
                submission_started = True
                post_btn.click(force=True)
                page.wait_for_timeout(6000)

                if first_comment:
                    try:
                        print("[LinkedInAutomater] Posting first comment with value drop...")
                        comment_btns = page.locator('button[aria-label*="Comment" i], button.comment-button, button:has-text("Comment")')
                        if comment_btns.count() > 0:
                            comment_btns.first.click()
                            page.wait_for_timeout(2000)
                            comm_box = page.locator('div[role="textbox"][contenteditable="true"], div.ql-editor, div[aria-label*="comment" i]').first
                            if comm_box.is_visible():
                                comm_box.fill(first_comment)
                                page.wait_for_timeout(1000)
                                submit_comm = page.locator('button.comments-comment-box__submit-button, button:has-text("Comment")').first
                                if submit_comm.is_visible() and submit_comm.is_enabled():
                                    submit_comm.click()
                                    page.wait_for_timeout(3000)
                                    print("[LinkedInAutomater] ✅ Successfully posted first comment via browser!")
                    except Exception as ce:
                        print(f"[LinkedInAutomater] Note on browser first-comment: {ce}")

                print("[LinkedInAutomater] ✅ Successfully published post to LinkedIn!")

                return True, "Published to LinkedIn successfully!"



            except Exception as e:
                if submission_started:
                    self.last_post_outcome_unknown = True
                    return False, (
                        "LinkedIn browser submission outcome is unknown after clicking Post; "
                        "the topic was reserved to prevent an automatic duplicate."
                    )
                return False, f"LinkedIn browser automation error: {e}"

            finally:

                context.close()





    def reply_to_own_post_comments(
        self,
        max_replies: int = 5,
        already_replied: Optional[set] = None,
        replied_ids: Optional[List[str]] = None,
    ) -> Tuple[int, str]:
        """
        Scans the user's recent LinkedIn posts for unreplied comments,
        generates professional B2B engineering replies using AIGenerator, and posts them.
        """
        if self.dry_run:
            print(f"[LinkedInAutomater] [DRY RUN] Would scan and reply to comments on recent posts.")
            return 0, "[DRY RUN] Simulated comment replies"

        if already_replied is None:
            already_replied = set()
        if replied_ids is None:
            replied_ids = []

        if not self.is_browser_session_available():
            return 0, "LinkedIn session not available for browser commenting."

        replied_count = 0
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
                    print(f"[LinkedInAutomater] Error restoring cookies: {e}")

            page = context.pages[0] if context.pages else context.new_page()
            try:
                from src.ai_generator import AIGenerator
                ai = AIGenerator()

                print("[LinkedInAutomater] Navigating to recent activity page...")
                page.goto("https://www.linkedin.com/in/me/recent-activity/all/", wait_until="domcontentloaded", timeout=40000)
                page.wait_for_timeout(3500)

                if any(marker in page.url.lower() for marker in ("login", "checkpoint", "challenge", "authwall")):
                    return 0, "LinkedIn session expired or requires login."

                # Find comment buttons to expand comments on recent posts
                comment_triggers = page.locator('button[aria-label*="comment" i], button:has-text("Comment")').all()
                for btn in comment_triggers[:3]:
                    try:
                        if btn.is_visible():
                            btn.click(timeout=3000)
                            page.wait_for_timeout(1500)
                    except Exception:
                        pass

                # Locate comments containers
                comments = page.locator('article.comments-comment-item, div.comments-comment-item').all()
                print(f"[LinkedInAutomater] Found {len(comments)} comments on visible posts.")

                for comment in comments:
                    if replied_count >= max_replies:
                        break
                    reply_id = ""
                    reply_submission_started = False
                    try:
                        # Check if already replied by us in the visible DOM.
                        nested_replies = comment.locator('.comments-reply-item, .comments-comment-item__nested-comments').inner_text(timeout=1000)
                        nested_lower = nested_replies.lower()
                        if "vishnu gupta" in nested_lower or "neubench" in nested_lower:
                            continue
                    except Exception:
                        pass

                    try:
                        author_elem = comment.locator('.comments-post-meta__name-text, a[data-field="actor_name"]').first
                        author_name = author_elem.inner_text().strip() if author_elem.is_visible() else "Colleague"
                        if "Vishnu Gupta" in author_name or "NeuBench" in author_name:
                            continue  # Do not reply to self

                        text_elem = comment.locator('.comments-comment-item__main-content, .update-components-text').first
                        comment_text = text_elem.inner_text().strip() if text_elem.is_visible() else ""
                        if not comment_text or len(comment_text) < 3:
                            continue

                        parent_key = ""
                        post_context = "NeuBench LinkedIn post"
                        for parent_selector in (
                            "xpath=ancestor::article[1]",
                            "xpath=ancestor::div[contains(@class, 'feed-shared-update-v2')][1]",
                        ):
                            try:
                                parent = comment.locator(parent_selector).first
                                parent_key = self._extract_post_key(parent)
                                try:
                                    post_context = parent.inner_text(timeout=1000)[:350]
                                except Exception:
                                    pass
                                if parent_key:
                                    break
                            except Exception:
                                continue
                        parent_key = parent_key or "own-post"
                        reply_id = engagement_key(
                            "own_reply", parent_key, author_name, comment_text
                        )
                        if reply_id in already_replied:
                            continue

                        print(f"[LinkedInAutomater] Replying to comment by {author_name}: \"{comment_text[:50]}...\"")
                        reply_text = ai.generate_linkedin_comment_reply(
                            post_text=post_context,
                            commenter_name=author_name,
                            comment_text=comment_text,
                        )

                        # Click Reply button inside this comment
                        reply_btn = comment.locator('button[aria-label*="Reply" i], button:has-text("Reply")').first
                        if reply_btn.is_visible():
                            reply_btn.click(timeout=3000)
                            page.wait_for_timeout(1000)

                            # Find comment input box
                            reply_input = page.locator('div[role="textbox"][contenteditable="true"]').last
                            if reply_input.is_visible():
                                reply_input.click()
                                page.keyboard.insert_text(reply_text)
                                page.wait_for_timeout(1500)

                                # Submit reply
                                submit_btn = page.locator('button.comments-comment-box__submit-button, button:has-text("Reply")').last
                                if submit_btn.is_visible():
                                    reply_submission_started = True
                                    submit_btn.click(timeout=4000)
                                    replied_count += 1
                                    replied_ids.append(reply_id)
                                    already_replied.add(reply_id)
                                    print(f"[LinkedInAutomater] ✅ Successfully replied to {author_name}!")
                                    page.wait_for_timeout(3000)
                    except Exception as e:
                        if reply_submission_started and reply_id and reply_id not in replied_ids:
                            replied_count += 1
                            replied_ids.append(reply_id)
                            already_replied.add(reply_id)
                            print(f"[LinkedInAutomater] Reply submission outcome unknown for {author_name}; reserving target.")
                        print(f"[LinkedInAutomater] Error handling comment: {e}")
                        continue

                return replied_count, f"Replied to {replied_count} comments on recent posts."
            except Exception as e:
                return replied_count, f"LinkedIn comment reply error: {e}"
            finally:
                context.close()

    def _extract_post_key(self, post_elem) -> str:
        """Returns a stable identifier for a feed post (permalink/activity URN or text hash)."""
        for attr in ("data-urn", "data-activity-urn", "data-id"):
            try:
                value = post_elem.get_attribute(attr) or ""
                if value:
                    return value.strip()
            except Exception:
                continue
        try:
            link = post_elem.locator('a[href*="/feed/update/"], a[href*="urn:li:activity"]').first
            href = link.get_attribute("href") or ""
            if href:
                return href.split("?")[0].rstrip("/")
        except Exception:
            pass
        try:
            text = post_elem.inner_text().strip()
            if text:
                return "text:" + hashlib.md5(text[:400].encode("utf-8")).hexdigest()
        except Exception:
            pass
        return ""

    def _extract_social_counts(self, post_elem) -> Tuple[int, int, bool]:
        """Parses reactions/comments from a feed card. Returns (reactions, comments, parsed)."""
        counts_text = ""
        try:
            counts_text = post_elem.locator(
                '.social-details-social-counts, .social-details-social-counts__social-proof-container, [data-view-name="feed-social-counts"]'
            ).first.inner_text(timeout=1000)
        except Exception:
            counts_text = ""

        if not counts_text:
            return 0, 0, False

        text = counts_text.lower().replace(",", "")
        reactions = 0
        comments = 0
        m = re.search(r"(\d+)\s+(?:reactions?|likes?)", text)
        if m:
            reactions = int(m.group(1))
        m = re.search(r"(\d+)\s+comments?", text)
        if m:
            comments = int(m.group(1))
        return reactions, comments, bool(m or reactions)

    def _extract_author_name(self, post_elem) -> str:
        for sel in (
            '.update-components-actor__title span[aria-hidden="true"]',
            '.feed-shared-actor__name',
            'a[data-field="actor_name"]',
            '.update-components-actor__name',
        ):
            try:
                name = post_elem.locator(sel).first.inner_text(timeout=800).strip()
                if name:
                    return name.split("\n")[0][:60]
            except Exception:
                continue
        return "there"

    def _is_suitable_post(self, post_text: str) -> bool:
        lower = post_text.lower()
        if len(post_text.strip()) < 80:
            return False
        if any(bad in lower for bad in SUITABILITY_BLOCKLIST):
            return False
        if "vishnu gupta" in lower or "neubench" in lower:
            return False
        return True

    def _is_achievement_post(self, post_text: str) -> bool:
        lower = post_text.lower()
        return any(keyword in lower for keyword in ACHIEVEMENT_KEYWORDS)

    def _try_reply_to_question(
        self,
        page,
        post_elem,
        ai,
        already_replied: Optional[set] = None,
    ) -> Optional[str]:
        """Best-effort reply to a genuine question in the comments. Returns a reply key on success."""
        if already_replied is None:
            already_replied = set()
        try:
            comments = post_elem.locator(
                'article.comments-comment-item, div.comments-comment-item, article.comments-comment-entity'
            ).all()
        except Exception:
            return None

        for comment in comments[:4]:
            reply_key = ""
            reply_submission_started = False
            try:
                body_elem = comment.locator(
                    '.comments-comment-item__main-content, .update-components-text, .comments-comment-entity__content'
                ).first
                body = body_elem.inner_text(timeout=1000).strip()
                if not body or "?" not in body or len(body) < 15:
                    continue
                if "vishnu gupta" in body.lower() or "neubench" in body.lower():
                    continue

                author = "there"
                try:
                    author_elem = comment.locator('.comments-post-meta__name-text, a[data-field="actor_name"]').first
                    if author_elem.is_visible():
                        author = author_elem.inner_text().strip().split("\n")[0][:50] or "there"
                except Exception:
                    pass

                post_key = self._extract_post_key(post_elem) or "peer-post"
                reply_key = engagement_key("reply", post_key, author, body)
                if reply_key in already_replied:
                    continue

                reply_btn = comment.locator('button[aria-label*="Reply" i], button:has-text("Reply")').first
                if not reply_btn.is_visible():
                    continue

                reply_btn.click(timeout=3000)
                page.wait_for_timeout(1000)

                box = page.locator('div[role="textbox"][contenteditable="true"]').last
                if not box.is_visible():
                    continue

                reply_text = ai.generate_linkedin_comment_reply(
                    post_text=body, commenter_name=author, comment_text=body
                )
                box.click()
                page.keyboard.insert_text(reply_text)
                page.wait_for_timeout(1500)

                submit = page.locator('button.comments-comment-box__submit-button, button:has-text("Reply")').last
                if submit.is_visible():
                    reply_submission_started = True
                    submit.click(timeout=4000)
                    page.wait_for_timeout(3000)
                    return reply_key
            except Exception:
                if reply_submission_started and reply_key:
                    already_replied.add(reply_key)
                    return reply_key
                continue
        return None

    def engage_with_peer_posts(
        self,
        max_comments: int = 2,
        max_replies: int = 1,
        max_total: Optional[int] = None,
        already_commented: Optional[set] = None,
        already_replied: Optional[set] = None,
        commented_ids: Optional[List[str]] = None,
        replied_ids: Optional[List[str]] = None,
    ) -> Tuple[int, str]:
        """
        Navigates to the live LinkedIn feed, finds genuinely viral posts, and leaves
        suitable comments (congratulations for milestones, insight otherwise). Also
        replies to a genuine question in the comments when one is available.
        """
        if self.dry_run:
            print(f"[LinkedInAutomater] [DRY RUN] Would engage with viral LinkedIn posts and commenters.")
            return 0, "[DRY RUN] Simulated viral engagement"

        if already_commented is None:
            already_commented = set()
        if already_replied is None:
            already_replied = set()
        if commented_ids is None:
            commented_ids = []
        if replied_ids is None:
            replied_ids = []

        if not self.is_browser_session_available():
            return 0, "LinkedIn session not available for peer engagement."

        commented_count = 0

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
                    with open(cookie_file, "r", encoding="utf-8") as f:
                        c_data = json.load(f)
                        raw_cookies = c_data.get("cookies", c_data) if isinstance(c_data, dict) else c_data
                        if isinstance(raw_cookies, list):
                            all_cookies = [{k: v for k, v in c.items() if k in ["name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite"]} for c in raw_cookies]
                            context.add_cookies(all_cookies)
                except Exception as e:
                    print(f"[LinkedInAutomater] Error restoring cookies: {e}")

            page = context.pages[0] if context.pages else context.new_page()
            try:
                from src.ai_generator import AIGenerator
                ai = AIGenerator()

                feed_url = "https://www.linkedin.com/feed/"
                print(f"[LinkedInAutomater] Navigating to live feed: {feed_url} ...")
                page.goto(feed_url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(5000)

                if any(marker in page.url.lower() for marker in ("login", "checkpoint", "challenge", "authwall")):
                    return 0, "LinkedIn browser session expired or requires login."

                # Scroll down slightly to trigger lazy-loaded feed items
                page.mouse.wheel(0, 800)
                page.wait_for_timeout(3000)

                # Find top active feed post cards
                post_cards = page.locator('div[data-view-name="feed-full-update"], div.feed-shared-update-v2, article').all()
                print(f"[LinkedInAutomater] Found {len(post_cards)} candidate feed posts.")

                replies_count = 0
                for idx, post_elem in enumerate(post_cards[:12]):
                    if max_total is not None and commented_count + replies_count >= max_total:
                        break
                    if commented_count >= max_comments and replies_count >= max_replies:
                        break
                    post_key = ""
                    comment_submission_started = False
                    try:
                        post_text = post_elem.inner_text().strip()
                        if not self._is_suitable_post(post_text):
                            continue

                        post_key = self._extract_post_key(post_elem)
                        if not post_key or post_key in already_commented:
                            continue

                        reactions, comment_count, parsed = self._extract_social_counts(post_elem)
                        if parsed and reactions < 50 and comment_count < 10:
                            print(f"[LinkedInAutomater] Skipping low-engagement post ({reactions} reactions, {comment_count} comments).")
                            continue

                        if commented_count >= max_comments:
                            continue

                        # Find Comment button on this update
                        comment_btn = post_elem.locator('button[aria-label*="comment" i], button:has-text("Comment")').first
                        if not comment_btn.is_visible():
                            continue

                        comment_btn.scroll_into_view_if_needed(timeout=3000)
                        comment_btn.click(timeout=3000)
                        page.wait_for_timeout(2000)

                        # Locate comment text box
                        box = post_elem.locator('div[role="textbox"][contenteditable="true"]').first
                        if not box.is_visible():
                            box = page.locator('div[role="textbox"][contenteditable="true"]').last

                        if not box.is_visible():
                            continue

                        author_name = self._extract_author_name(post_elem)
                        if self._is_achievement_post(post_text):
                            comm_text = ai.generate_linkedin_congrats_comment(post_author=author_name, post_text=post_text)
                            kind = "congratulations"
                        else:
                            comm_text = ai.generate_linkedin_peer_comment(post_author=author_name, post_text=post_text)
                            kind = "insight"

                        print(f"[LinkedInAutomater] Drafted {kind} comment for {author_name}: {comm_text[:70]}...")

                        box.click()
                        page.keyboard.insert_text(comm_text)
                        page.wait_for_timeout(2000)

                        submit = post_elem.locator('button.comments-comment-box__submit-button, button:has-text("Comment")').first
                        if submit.is_visible():
                            comment_submission_started = True
                            submit.click(timeout=4000)
                            commented_count += 1
                            commented_ids.append(post_key)
                            already_commented.add(post_key)
                            print(f"[LinkedInAutomater] ✅ {kind.title()} comment posted on viral feed post #{idx+1}!")
                            page.wait_for_timeout(4000)

                            if replies_count < max_replies and (
                                max_total is None or commented_count + replies_count < max_total
                            ):
                                reply_key = self._try_reply_to_question(
                                    page,
                                    post_elem,
                                    ai,
                                    already_replied=already_replied,
                                )
                                if reply_key:
                                    replies_count += 1
                                    replied_ids.append(reply_key)
                                    already_replied.add(reply_key)
                                    print("[LinkedInAutomater] ✅ Replied to a question in that post's comments.")
                    except Exception as ex:
                        if comment_submission_started and post_key and post_key not in commented_ids:
                            commented_count += 1
                            commented_ids.append(post_key)
                            already_commented.add(post_key)
                            print(f"[LinkedInAutomater] Comment submission outcome unknown; reserving post #{idx+1}.")
                        print(f"[LinkedInAutomater] Error on post #{idx+1}: {ex}")
                        continue

                return commented_count, f"Commented on {commented_count} viral posts and replied to {replies_count} comments."
            except Exception as e:
                return commented_count, f"LinkedIn feed engagement error: {e}"
            finally:
                context.close()
