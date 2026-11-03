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
        self.last_outcome_unknown = False
        self.last_message = ""

    def is_session_available(self) -> bool:
        """Checks if a saved Instagram session with valid cookies exists."""
        cookie_file = self.user_data_dir / "cookies.json"
        return cookie_file.exists()

    def _select_crop_ratio(self, page, preferred_ratios: List[str]):
        """Selects aspect ratio in Instagram web composer to avoid automatic square cropping."""
        try:
            crop_trigger = page.locator('div[role="dialog"] svg[aria-label="Select crop"], div[role="dialog"] button:has(svg[aria-label="Select crop"]), div[role="dialog"] svg[aria-label="Crop"]').first
            if crop_trigger.is_visible(timeout=3000):
                crop_trigger.click()
                page.wait_for_timeout(800)
                selected = False
                for ratio in preferred_ratios:
                    opt = page.locator(f'div[role="dialog"] span:text-is("{ratio}"), div[role="dialog"] button:has-text("{ratio}"), div[role="dialog"] div:text-is("{ratio}")').first
                    if opt.is_visible(timeout=1500):
                        opt.click()
                        page.wait_for_timeout(800)
                        print(f"[InstagramAutomater] ✅ Set aspect ratio to {ratio}")
                        selected = True
                        break
                if not selected:
                    crop_trigger.click()
                    page.wait_for_timeout(400)
        except Exception as ex:
            print(f"[InstagramAutomater] Aspect ratio selection note: {ex}")

    def post_carousel(self, image_paths: List[str], caption: str) -> Tuple[bool, str]:
        """Publishes multi-slide carousel images to Instagram (@neubench)."""
        self.last_outcome_unknown = False
        self.last_message = ""
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
            browser = p.chromium.launch(
                headless=self.headless,
                args=args
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
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

            page = context.new_page()

            try:
                print("[InstagramAutomater] Navigating to https://www.instagram.com/ ...")
                page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=40000)
                page.wait_for_timeout(4000)
                if "login" in page.url.lower():
                    return False, "Instagram session expired or requires login."

                # Dismiss 'Not Now' notification popups
                for dismiss_text in ["Not Now", "Cancel", "Decline optional cookies"]:
                    try:
                        btn = page.locator(f'button:has-text("{dismiss_text}")')
                        if btn.is_visible(timeout=1500):
                            btn.click()
                            page.wait_for_timeout(1000)
                    except Exception:
                        pass

                # 1. Click Create button in navigation menu
                print("[InstagramAutomater] Opening Create menu...")
                create_link = page.locator('svg[aria-label="New post"]').locator('xpath=ancestor::a | ancestor::div[role="button"]').first
                create_link.click()
                page.wait_for_timeout(1500)

                # 2. Click 'Post' option in the Create dropdown
                post_item = page.locator('span:text-is("Post")').first
                post_item.wait_for(state="visible", timeout=10000)
                post_item.click()
                page.wait_for_timeout(2500)

                # 3. Upload images
                print(f"[InstagramAutomater] Uploading {len(valid_images)} carousel slides...")
                file_input = page.locator('div[role="dialog"] input[type="file"], input[type="file"]').first
                file_input.wait_for(state="attached", timeout=15000)
                file_input.set_input_files(valid_images)
                page.wait_for_timeout(4000)

                # 3b. Select Original / 4:5 aspect ratio so slides are never cropped
                self._select_crop_ratio(page, ["Original", "4:5"])

                # 4. First 'Next' button (Top right of dialog: Crop step)
                next_btn = page.locator('div[role="dialog"] div:text-is("Next"), div[role="dialog"] button:has-text("Next")').last
                next_btn.click()
                page.wait_for_timeout(3500)

                # 5. Second 'Next' button (Filters step)
                next_btn2 = page.locator('div[role="dialog"] div:text-is("Next"), div[role="dialog"] button:has-text("Next")').last
                next_btn2.click()
                page.wait_for_timeout(3500)

                # 6. Write caption in dialog textbox
                print("[InstagramAutomater] Entering caption...")
                caption_area = page.locator('div[role="dialog"] [aria-label*="caption" i], div[role="dialog"] div[role="textbox"]').first
                caption_area.click()
                page.wait_for_timeout(500)
                caption_area.fill(caption)
                page.wait_for_timeout(1500)

                # 6b. Advanced Settings: Hide Like and View Counts by default
                try:
                    print("[InstagramAutomater] Enabling 'Hide like and view counts' in Advanced settings...")
                    adv_btn = page.locator('div[role="dialog"] span:has-text("Advanced settings"), div[role="dialog"] div:has-text("Advanced settings")').last
                    if adv_btn.count() > 0:
                        adv_btn.click()
                        page.wait_for_timeout(1000)
                        # Locate the toggle checkbox/switch for hiding like count
                        hide_likes_switch = page.locator('div[role="dialog"] input[type="checkbox"], div[role="dialog"] [role="switch"]').first
                        if hide_likes_switch.count() > 0:
                            is_checked = hide_likes_switch.is_checked() if hasattr(hide_likes_switch, 'is_checked') else False
                            if not is_checked:
                                hide_likes_switch.click()
                                print("[InstagramAutomater] ✅ Hidden like and view counts enabled.")
                except Exception as ex:
                    print(f"[InstagramAutomater] Note on advanced settings toggle: {ex}")

                # 7. Click 'Share' button
                print("[InstagramAutomater] Clicking Share button...")
                share_btn = page.locator('div[role="dialog"] div:text-is("Share"), div[role="dialog"] button:has-text("Share")').last
                share_btn.click()

                # 8. Await post confirmation
                print("[InstagramAutomater] Waiting for upload confirmation...")
                try:
                    page.wait_for_selector('text="Your post has been shared.", text="Post shared."', timeout=45000)
                except Exception:
                    self.last_outcome_unknown = True
                    self.last_message = "Instagram carousel submission was not confirmed; retry blocked."
                    return False, self.last_message

                print("[InstagramAutomater] ✅ Successfully published carousel to Instagram (@neubench)!")
                self.last_message = "Published carousel to Instagram (@neubench)"
                return True, self.last_message

            except Exception as e:
                print(f"[InstagramAutomater] ❌ Publish failed: {e}")
                self.last_message = f"Instagram publish error: {e}"
                return False, self.last_message
            finally:
                context.close()
                browser.close()

    def post_reel(self, video_path: str, caption: str) -> Tuple[bool, str]:
        """Publishes a 9:16 vertical video reel directly to Instagram (@neubench)."""
        self.last_outcome_unknown = False
        self.last_message = ""
        if self.dry_run:
            print(f"[InstagramAutomater] [DRY RUN] Would post Reel: {video_path} with caption: {caption[:60]}...")
            return True, "Simulated Instagram Reel"

        if not self.is_session_available():
            return False, "Instagram session not authenticated. Run 'python main.py login-instagram'."

        resolved_video = Path(video_path).resolve()
        if not resolved_video.exists():
            return False, f"Video file not found: {video_path}"

        cookie_file = self.user_data_dir / "cookies.json"

        with sync_playwright() as p:
            args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars"
            ]
            browser = p.chromium.launch(
                headless=self.headless,
                args=args
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )

            if cookie_file.exists():
                try:
                    with open(cookie_file, "r", encoding="utf-8") as f:
                        c_data = json.load(f)
                        raw_cookies = c_data.get("cookies", c_data) if isinstance(c_data, dict) else c_data
                        if isinstance(raw_cookies, list):
                            context.add_cookies(raw_cookies)
                except Exception as e:
                    print(f"[InstagramAutomater] Cookie restore note: {e}")

            page = context.new_page()

            try:
                print("[InstagramAutomater] Navigating to https://www.instagram.com/ ...")
                page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=40000)
                page.wait_for_timeout(4000)
                if "login" in page.url.lower():
                    return False, "Instagram session expired or requires login."

                for dismiss_text in ["Not Now", "Cancel", "Decline optional cookies"]:
                    try:
                        btn = page.locator(f'button:has-text("{dismiss_text}")')
                        if btn.is_visible(timeout=1500):
                            btn.click()
                            page.wait_for_timeout(1000)
                    except Exception:
                        pass

                # 1. Click Create button in navigation menu
                print("[InstagramAutomater] Opening Create menu...")
                create_link = page.locator('svg[aria-label="New post"]').locator('xpath=ancestor::a | ancestor::div[role="button"]').first
                create_link.click()
                page.wait_for_timeout(1500)

                # 2. Click 'Post' option
                post_item = page.locator('span:text-is("Post")').first
                if post_item.is_visible(timeout=5000):
                    post_item.click()
                    page.wait_for_timeout(2500)

                # 3. Upload Reel Video
                print(f"[InstagramAutomater] Uploading Reel video: {resolved_video.name}...")
                file_input = page.locator('div[role="dialog"] input[type="file"], input[type="file"]').first
                file_input.wait_for(state="attached", timeout=15000)
                file_input.set_input_files(str(resolved_video))
                page.wait_for_timeout(6000)

                # Dismiss 'Video posts are now shared as reels' notice if it appears
                try:
                    ok_btn = page.locator('div[role="dialog"] button:has-text("OK"), button:has-text("OK")').first
                    if ok_btn.is_visible(timeout=3000):
                        ok_btn.click()
                        page.wait_for_timeout(1500)
                except Exception:
                    pass

                # 3b. Select 9:16 / Original vertical aspect ratio so Reel is never cropped to square
                self._select_crop_ratio(page, ["9:16", "Original"])

                # 4. First 'Next' button (Crop/Ratio step)
                next_btn = page.locator('div[role="dialog"] div:text-is("Next"), div[role="dialog"] button:has-text("Next")').last
                next_btn.click()
                page.wait_for_timeout(3500)

                # 5. Second 'Next' button (Cover frame / Audio step)
                next_btn2 = page.locator('div[role="dialog"] div:text-is("Next"), div[role="dialog"] button:has-text("Next")').last
                next_btn2.click()
                page.wait_for_timeout(3500)

                # 6. Write caption
                print("[InstagramAutomater] Entering caption...")
                caption_area = page.locator('div[role="dialog"] [aria-label*="caption" i], div[role="dialog"] div[role="textbox"]').first
                caption_area.click()
                page.wait_for_timeout(500)
                caption_area.fill(caption)
                page.wait_for_timeout(1500)

                # 6b. Hide Like and View counts
                try:
                    print("[InstagramAutomater] Enabling 'Hide like and view counts' in Advanced settings...")
                    adv_btn = page.locator('div[role="dialog"] span:has-text("Advanced settings"), div[role="dialog"] div:has-text("Advanced settings")').last
                    if adv_btn.count() > 0:
                        adv_btn.click()
                        page.wait_for_timeout(1000)
                        hide_likes_switch = page.locator('div[role="dialog"] input[type="checkbox"], div[role="dialog"] [role="switch"]').first
                        if hide_likes_switch.count() > 0:
                            is_checked = hide_likes_switch.is_checked() if hasattr(hide_likes_switch, 'is_checked') else False
                            if not is_checked:
                                hide_likes_switch.click()
                                print("[InstagramAutomater] ✅ Hidden like and view counts enabled for Reel.")
                except Exception as ex:
                    print(f"[InstagramAutomater] Note on advanced settings: {ex}")

                # 7. Click 'Share' button
                print("[InstagramAutomater] Clicking Share button...")
                share_btn = page.locator('div[role="dialog"] div:text-is("Share"), div[role="dialog"] button:has-text("Share")').last
                share_btn.click()

                # 8. Await post confirmation
                print("[InstagramAutomater] Waiting for Reel upload confirmation...")
                try:
                    page.wait_for_selector('text="Your reel has been shared.", text="Your post has been shared.", text="Post shared."', timeout=60000)
                except Exception:
                    self.last_outcome_unknown = True
                    self.last_message = "Instagram Reel submission was not confirmed; retry blocked."
                    return False, self.last_message

                print("[InstagramAutomater] ✅ Successfully published Reel to Instagram (@neubench)!")
                self.last_message = "Published Reel to Instagram (@neubench)"
                return True, self.last_message

            except Exception as e:
                print(f"[InstagramAutomater] ❌ Reel publish failed: {e}")
                self.last_message = f"Instagram Reel error: {e}"
                return False, self.last_message
            finally:
                context.close()
                browser.close()

