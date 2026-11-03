import sys
import os
import time
import random

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.sync_api import sync_playwright, BrowserContext
import config
from src.x_state import prepare_x_text

class TwitterClient:
    """Automates X interactions safely with stealth, human typing jitter, and storage state."""

    def __init__(self, headless: bool = True, dry_run: bool = False):
        self.headless = headless
        self.dry_run = dry_run
        self.user_data_dir = str(config.USER_DATA_DIR)
        self.last_outcome = "not_attempted"
        self.last_outcome_unknown = False
        self.last_message = ""

    def _reset_outcome(self):
        self.last_outcome = "not_attempted"
        self.last_outcome_unknown = False
        self.last_message = ""

    def _finish_outcome(self, outcome: str, message: str) -> bool:
        self.last_outcome = outcome
        self.last_outcome_unknown = outcome == "unknown"
        self.last_message = message
        return outcome in {"success", "dry_run"}

    @staticmethod
    def _response_confirms_tweet(response) -> bool:
        """Return true only for a successful CreateTweet response."""

        if "CreateTweet" not in getattr(response, "url", ""):
            return False
        if getattr(response, "status", 0) != 200:
            return False
        try:
            payload = response.json()
        except Exception:
            # Some Playwright response doubles and X responses do not expose a
            # JSON body. A 200 CreateTweet response is still a valid signal.
            return True
        return not (isinstance(payload, dict) and payload.get("errors"))

    def _install_tweet_response_listener(self, page):
        state = {"confirmed": False, "failed": False}

        def on_response(response):
            if "CreateTweet" not in getattr(response, "url", ""):
                return
            if getattr(response, "status", 0) == 200:
                if self._response_confirms_tweet(response):
                    state["confirmed"] = True
                else:
                    state["failed"] = True

        page.on("response", on_response)
        return state

    @staticmethod
    def _page_has_success_toast(page) -> bool:
        try:
            messages = page.locator('[role="alert"], [data-testid="toast"]').all_inner_texts()
            text = " ".join(messages).lower()
            return any(
                phrase in text
                for phrase in ("post was sent", "post sent", "tweet sent", "your post was sent")
            )
        except Exception:
            return False

    def _wait_for_tweet_confirmation(self, page, state, timeout_ms: int = 15000) -> bool:
        for _ in range(max(1, timeout_ms // 500)):
            if state["confirmed"] or self._page_has_success_toast(page):
                return True
            if state["failed"]:
                return False
            page.wait_for_timeout(500)
        return state["confirmed"] or self._page_has_success_toast(page)

    def _get_context_and_browser(self, p):
        """Launches context with anti-detect flags and saved storage state."""
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars"
        ]
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        
        if config.COOKIES_FILE.exists():
            browser = p.chromium.launch(headless=self.headless, args=args)
            context = browser.new_context(
                storage_state=str(config.COOKIES_FILE),
                viewport={"width": 1280, "height": 850},
                user_agent=user_agent
            )
            return context, browser
        else:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                viewport={"width": 1280, "height": 850},
                args=args,
                user_agent=user_agent
            )
            return context, None

    def _human_type(self, element, text: str):
        """Types text with randomized human-like delay between keystrokes."""
        try:
            element.click(force=True, timeout=5000)
        except Exception:
            try:
                element.focus()
            except Exception:
                pass
        time.sleep(random.uniform(0.3, 0.7))
        for char in text:
            element.type(char)
            time.sleep(random.uniform(0.03, 0.08))
        time.sleep(random.uniform(0.5, 1.2))

    def is_logged_in(self) -> bool:
        """Verifies if the saved session is valid and logged in."""
        with sync_playwright() as p:
            context, browser = self._get_context_and_browser(p)
            page = context.pages[0] if context.pages else context.new_page()
            try:
                page.goto("https://x.com/home", timeout=30000)
                page.wait_for_timeout(3000)
                if "login" in page.url.lower():
                    return False
                return page.locator('[data-testid="SideNav_NewTweet_Button"]').count() > 0 or \
                       page.locator('[data-testid="primaryColumn"]').count() > 0
            except Exception:
                return False
            finally:
                context.close()
                if browser:
                    browser.close()

    def post_tweet(self, text: str, media_path: Optional[str] = None) -> bool:
        """Publishes an original tweet."""
        self._reset_outcome()
        if self.dry_run:
            print(f"[TwitterClient] [DRY RUN] Would publish original tweet: {text}")
            return self._finish_outcome("dry_run", "[DRY RUN] Tweet simulated.")

        text = prepare_x_text(text)
        if not text:
            return self._finish_outcome("failed", "X post text is empty.")

        with sync_playwright() as p:
            context = None
            browser = None
            submission_started = False
            try:
                context, browser = self._get_context_and_browser(p)
                page = context.pages[0] if context.pages else context.new_page()
                response_state = self._install_tweet_response_listener(page)

                print(f"[TwitterClient] Navigating to compose tweet...")
                page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=35000)
                try:
                    page.wait_for_selector('[data-testid="tweetTextarea_0"], div[role="textbox"]', timeout=20000)
                except Exception:
                    print("[TwitterClient] Retrying compose via x.com/home...")
                    page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_selector('[data-testid="tweetTextarea_0"], div[role="textbox"]', timeout=15000)
                
                textarea = page.locator('[data-testid="tweetTextarea_0"], div[role="textbox"]').first
                self._human_type(textarea, text)

                if media_path and os.path.exists(media_path):
                    try:
                        print(f"[TwitterClient] Attaching media: {media_path}...")
                        file_input = page.locator('input[type="file"][data-testid="fileInput"]').first
                        file_input.set_input_files(media_path)
                        page.wait_for_timeout(5000)
                    except Exception as ex:
                        print(f"[TwitterClient] Media attach notice: {ex}")

                post_btn = page.locator('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]').first
                time.sleep(random.uniform(1.0, 2.0))

                # Verify button is enabled
                is_disabled = post_btn.get_attribute("aria-disabled") == "true" or post_btn.is_disabled()
                if is_disabled:
                    print("[TwitterClient] ⚠️ Post button is disabled. Retrying with ultra-concise text...")
                    textarea.fill("")
                    short_text = prepare_x_text(text[:230])
                    self._human_type(textarea, short_text)
                    page.wait_for_timeout(1000)
                    is_disabled = post_btn.get_attribute("aria-disabled") == "true" or post_btn.is_disabled()
                    if is_disabled:
                        return self._finish_outcome("failed", "X post button remained disabled.")

                # Submit via native Control+Enter keyboard shortcut to bypass overlay pointer intercepts
                print("[TwitterClient] Submitting tweet via Control+Enter keyboard shortcut...")
                try:
                    textarea.focus()
                except Exception:
                    pass
                submission_started = True
                page.keyboard.press("Control+Enter")

                # Fallback: attempt direct button click and dispatch_event
                time.sleep(1.0)
                if not response_state["confirmed"] and not response_state["failed"]:
                    try:
                        submission_started = True
                        post_btn.click(force=True, timeout=3000)
                    except Exception:
                        try:
                            submission_started = True
                            post_btn.dispatch_event("click")
                        except Exception:
                            pass

                # Await network confirmation
                confirmed = self._wait_for_tweet_confirmation(page, response_state)
                if confirmed:
                    print(f"[TwitterClient] ✅ Tweet posted successfully (network verified): {text[:60]}...")
                    return self._finish_outcome("success", "Tweet published and confirmed by X.")
                if response_state["failed"]:
                    return self._finish_outcome("failed", "X rejected the tweet submission.")
                if submission_started:
                    return self._finish_outcome(
                        "unknown",
                        "X submission timed out after the browser sent it; retry blocked to prevent duplicates.",
                    )
                return self._finish_outcome("failed", "X did not confirm the tweet submission.")
            except Exception as e:
                print(f"[TwitterClient] ❌ Failed to post tweet: {e}")
                outcome = "unknown" if submission_started else "failed"
                return self._finish_outcome(outcome, str(e))
            finally:
                if context:
                    context.close()
                if browser:
                    browser.close()

    def post_reply(self, tweet_url: str, reply_text: str) -> bool:
        """Publishes a reply under a target viral tweet."""
        self._reset_outcome()
        if self.dry_run:
            print(f"[TwitterClient] [DRY RUN] Would reply to {tweet_url}: {reply_text}")
            return self._finish_outcome("dry_run", "[DRY RUN] Reply simulated.")

        reply_text = prepare_x_text(reply_text)
        if not tweet_url or not reply_text:
            return self._finish_outcome("failed", "X reply URL or text is empty.")

        with sync_playwright() as p:
            context = None
            browser = None
            submission_started = False
            try:
                context, browser = self._get_context_and_browser(p)
                page = context.pages[0] if context.pages else context.new_page()
                response_state = self._install_tweet_response_listener(page)
                print(f"[TwitterClient] Opening tweet for reply: {tweet_url}")
                page.goto(tweet_url, wait_until="domcontentloaded", timeout=35000)
                
                # Wait for tweet shell and click reply action button to open composer modal
                page.wait_for_selector('[data-testid="reply"]', timeout=20000)
                page.locator('[data-testid="reply"]').first.click()
                page.wait_for_timeout(1500)

                # Wait for active reply textarea in modal dialog (avoid background mask intercept)
                page.wait_for_selector('div[role="dialog"] div[role="textbox"], [data-testid="tweetTextarea_0"]', timeout=15000)
                reply_box = page.locator('div[role="dialog"] div[role="textbox"], [data-testid="tweetTextarea_0"]').first
                self._human_type(reply_box, reply_text)

                reply_btn = page.locator('div[role="dialog"] [data-testid="tweetButton"], [data-testid="tweetButtonInline"]').first
                time.sleep(random.uniform(0.8, 1.8))
                try:
                    submission_started = True
                    reply_btn.click(force=True, timeout=10000)
                except Exception:
                    try:
                        submission_started = True
                        reply_btn.dispatch_event("click")
                    except Exception:
                        pass
                
                confirmed = self._wait_for_tweet_confirmation(page, response_state)
                if confirmed:
                    print(f"[TwitterClient] ✅ Reply posted successfully!")
                    return self._finish_outcome("success", "Reply published and confirmed by X.")
                if response_state["failed"]:
                    return self._finish_outcome("failed", "X rejected the reply submission.")
                if submission_started:
                    return self._finish_outcome(
                        "unknown",
                        "X reply submission timed out; retry blocked to prevent duplicates.",
                    )
                return self._finish_outcome("failed", "X did not confirm the reply submission.")
            except Exception as e:
                print(f"[TwitterClient] ❌ Failed to reply: {e}")
                outcome = "unknown" if submission_started else "failed"
                return self._finish_outcome(outcome, str(e))
            finally:
                if context:
                    context.close()
                if browser:
                    browser.close()

    def post_quote_tweet(self, tweet_url: str, quote_text: str) -> bool:
        """Publishes a Quote-Tweet ('repost with masala on top')."""
        self._reset_outcome()
        if self.dry_run:
            print(f"[TwitterClient] [DRY RUN] Would quote-tweet {tweet_url}: {quote_text}")
            return self._finish_outcome("dry_run", "[DRY RUN] Quote-tweet simulated.")

        quote_text = prepare_x_text(quote_text)
        if not tweet_url or not quote_text:
            return self._finish_outcome("failed", "X quote-tweet URL or text is empty.")

        with sync_playwright() as p:
            context = None
            browser = None
            submission_started = False
            try:
                context, browser = self._get_context_and_browser(p)
                page = context.pages[0] if context.pages else context.new_page()
                response_state = self._install_tweet_response_listener(page)
                print(f"[TwitterClient] Opening tweet for quote: {tweet_url}")
                page.goto(tweet_url, wait_until="domcontentloaded", timeout=35000)

                # Wait for retweet action button to open menu
                page.wait_for_selector('[data-testid="retweet"]', timeout=20000)
                page.locator('[data-testid="retweet"]').first.click()
                page.wait_for_timeout(1500)

                # Click "Quote" option in dropdown menu
                quote_option = page.locator('a[href*="/compose/post"], [role="menuitem"]:has-text("Quote"), div[role="menuitem"]:has-text("Quote")').first
                quote_option.wait_for(state="visible", timeout=10000)
                quote_option.click()
                page.wait_for_timeout(2000)

                # Type commentary in compose modal dialog
                page.wait_for_selector('div[role="dialog"] div[role="textbox"], [data-testid="tweetTextarea_0"]', timeout=15000)
                modal_textarea = page.locator('div[role="dialog"] div[role="textbox"], [data-testid="tweetTextarea_0"]').first
                self._human_type(modal_textarea, quote_text)

                # Click Post
                post_btn = page.locator('div[role="dialog"] [data-testid="tweetButton"], [data-testid="tweetButtonInline"]').first
                time.sleep(random.uniform(1.0, 2.0))
                try:
                    submission_started = True
                    post_btn.click(force=True, timeout=10000)
                except Exception:
                    try:
                        submission_started = True
                        post_btn.dispatch_event("click")
                    except Exception:
                        pass

                confirmed = self._wait_for_tweet_confirmation(page, response_state)
                if confirmed:
                    print(f"[TwitterClient] ✅ Quote-Tweet posted successfully!")
                    return self._finish_outcome("success", "Quote-tweet published and confirmed by X.")
                if response_state["failed"]:
                    return self._finish_outcome("failed", "X rejected the quote-tweet submission.")
                if submission_started:
                    return self._finish_outcome(
                        "unknown",
                        "X quote-tweet submission timed out; retry blocked to prevent duplicates.",
                    )
                return self._finish_outcome("failed", "X did not confirm the quote-tweet submission.")
            except Exception as e:
                print(f"[TwitterClient] ❌ Failed to quote tweet: {e}")
                outcome = "unknown" if submission_started else "failed"
                return self._finish_outcome(outcome, str(e))
            finally:
                if context:
                    context.close()
                if browser:
                    browser.close()

    def follow_account(self, username: str) -> bool:
        """Follows an account on X if not already followed."""
        if self.dry_run:
            print(f"[TwitterClient] [DRY RUN] Would follow @{username}")
            return True
        with sync_playwright() as p:
            context, browser = self._get_context_and_browser(p)
            page = context.pages[0] if context.pages else context.new_page()
            try:
                page.goto(f"https://x.com/{username}", timeout=35000)
                page.wait_for_timeout(2500)
                follow_btn = page.locator('button[data-testid$="-follow"], [role="button"][data-testid$="-follow"]').first
                if follow_btn.is_visible(timeout=3000):
                    follow_btn.click(force=True)
                    page.wait_for_timeout(2000)
                    print(f"[TwitterClient] Successfully followed @{username}!")
                    return True
                else:
                    print(f"[TwitterClient] Already following @{username} or follow button unavailable.")
                    return True
            except Exception as e:
                print(f"[TwitterClient] Could not follow @{username}: {e}")
                return False
            finally:
                context.close()
                if browser:
                    browser.close()

    def get_latest_tweet_from_account(self, username: str) -> dict:
        """Fetches the latest tweet from a target viral account to snipe or quote."""
        with sync_playwright() as p:
            context, browser = self._get_context_and_browser(p)
            page = context.pages[0] if context.pages else context.new_page()
            try:
                profile_url = f"https://x.com/{username}"
                page.goto(profile_url, timeout=35000)
                page.wait_for_timeout(2500)

                # Check if user is blocked or unavailable
                body_text = page.inner_text("body")
                if "is blocked" in body_text or "Account suspended" in body_text:
                    print(f"[TwitterClient] Account @{username} is blocked or suspended. Skipping.")
                    return {}

                # Scroll down to trigger lazy loading of tweets past tall banners / live broadcasts
                page.evaluate("window.scrollBy(0, 600)")
                page.wait_for_timeout(2000)

                # Auto-follow viral target account if not yet followed
                try:
                    follow_btn = page.locator('button[data-testid$="-follow"], [role="button"][data-testid$="-follow"]').first
                    if follow_btn.is_visible(timeout=2000):
                        print(f"[TwitterClient] Auto-following @{username} for direct notification & reach...")
                        follow_btn.click(force=True)
                        page.wait_for_timeout(1000)
                except Exception:
                    pass

                # Wait for tweets with fallback selector
                page.wait_for_selector('article[data-testid="tweet"], article', timeout=12000)
                
                tweets = page.locator('article[data-testid="tweet"], article')
                if tweets.count() == 0:
                    return {}

                first_tweet = tweets.first
                tweet_text_el = first_tweet.locator('[data-testid="tweetText"]').first
                tweet_text = tweet_text_el.inner_text() if tweet_text_el.is_visible() else ""
                
                link_el = first_tweet.locator('a[href*="/status/"]').first
                href = link_el.get_attribute("href") if link_el else None
                tweet_url = f"https://x.com{href}" if href and not href.startswith("http") else href
                
                return {
                    "username": username,
                    "tweet_text": tweet_text,
                    "tweet_url": tweet_url
                }
            except Exception as e:
                print(f"[TwitterClient] Could not fetch tweet from @{username}: {e}")
                return {}
            finally:
                context.close()
                if browser:
                    browser.close()
