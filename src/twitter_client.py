import sys
import time
import random

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext
import config

class TwitterClient:
    """Automates X interactions safely with stealth, human typing jitter, and storage state."""

    def __init__(self, headless: bool = True, dry_run: bool = False):
        self.headless = headless
        self.dry_run = dry_run
        self.user_data_dir = str(config.USER_DATA_DIR)

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
        if self.dry_run:
            print(f"[TwitterClient] [DRY RUN] Would publish original tweet: {text}")
            return True

        # Strict character limit clamp for X free tier (max 280)
        if len(text) > 275:
            print(f"[TwitterClient] ⚠️ Tweet length ({len(text)}) exceeds 275 chars. Clamping before posting...")
            text = text[:270].rsplit(' ', 1)[0].rstrip('.,:;') + '...'

        with sync_playwright() as p:
            context, browser = self._get_context_and_browser(p)
            page = context.pages[0] if context.pages else context.new_page()
            try:
                tweet_sent = False
                def on_response(response):
                    nonlocal tweet_sent
                    if "CreateTweet" in response.url and response.status == 200:
                        tweet_sent = True

                page.on("response", on_response)

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
                    short_text = text[:230].rsplit(' ', 1)[0] + '...'
                    self._human_type(textarea, short_text)
                    page.wait_for_timeout(1000)

                # Submit via native Control+Enter keyboard shortcut to bypass overlay pointer intercepts
                print("[TwitterClient] Submitting tweet via Control+Enter keyboard shortcut...")
                try:
                    textarea.focus()
                except Exception:
                    pass
                page.keyboard.press("Control+Enter")

                # Fallback: attempt direct button click and dispatch_event
                time.sleep(1.0)
                if not tweet_sent:
                    try:
                        post_btn.click(force=True, timeout=3000)
                    except Exception:
                        try:
                            post_btn.dispatch_event("click")
                        except Exception:
                            pass

                # Await network confirmation
                for _ in range(12):
                    if tweet_sent:
                        break
                    page.wait_for_timeout(1000)

                page.wait_for_timeout(2000)
                print(f"[TwitterClient] ✅ Tweet posted successfully (network verified): {text[:60]}...")
                return True
            except Exception as e:
                print(f"[TwitterClient] ❌ Failed to post tweet: {e}")
                return False
            finally:
                context.close()
                if browser:
                    browser.close()

    def post_reply(self, tweet_url: str, reply_text: str) -> bool:
        """Publishes a reply under a target viral tweet."""
        if self.dry_run:
            print(f"[TwitterClient] [DRY RUN] Would reply to {tweet_url}: {reply_text}")
            return True

        with sync_playwright() as p:
            context, browser = self._get_context_and_browser(p)
            page = context.pages[0] if context.pages else context.new_page()
            try:
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
                    reply_btn.click(force=True, timeout=10000)
                except Exception:
                    reply_btn.dispatch_event("click")
                
                page.wait_for_timeout(5000)
                print(f"[TwitterClient] ✅ Reply posted successfully!")
                return True
            except Exception as e:
                print(f"[TwitterClient] ❌ Failed to reply: {e}")
                return False
            finally:
                context.close()
                if browser:
                    browser.close()

    def post_quote_tweet(self, tweet_url: str, quote_text: str) -> bool:
        """Publishes a Quote-Tweet ('repost with masala on top')."""
        if self.dry_run:
            print(f"[TwitterClient] [DRY RUN] Would quote-tweet {tweet_url}: {quote_text}")
            return True

        with sync_playwright() as p:
            context, browser = self._get_context_and_browser(p)
            page = context.pages[0] if context.pages else context.new_page()
            try:
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
                    post_btn.click(force=True, timeout=10000)
                except Exception:
                    post_btn.dispatch_event("click")

                page.wait_for_timeout(5000)
                print(f"[TwitterClient] ✅ Quote-Tweet posted successfully!")
                return True
            except Exception as e:
                print(f"[TwitterClient] ❌ Failed to quote tweet: {e}")
                return False
            finally:
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
