import time
import random
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext
import config

class TwitterClient:
    """Automates X interactions safely with stealth, human typing jitter, and storage state."""

    def __init__(self, headless: bool = True):
        self.headless = headless
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
        element.click()
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

    def post_tweet(self, text: str) -> bool:
        """Publishes an original tweet."""
        with sync_playwright() as p:
            context, browser = self._get_context_and_browser(p)
            page = context.pages[0] if context.pages else context.new_page()
            try:
                print(f"[TwitterClient] Navigating to compose tweet...")
                page.goto("https://x.com/compose/post", timeout=35000)
                page.wait_for_selector('[data-testid="tweetTextarea_0"], div[role="textbox"]', timeout=15000)
                
                textarea = page.locator('[data-testid="tweetTextarea_0"], div[role="textbox"]').first
                self._human_type(textarea, text)

                post_btn = page.locator('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]').first
                time.sleep(random.uniform(1.0, 2.0))
                post_btn.click()
                
                # Wait for modal to disappear or toast to show
                page.wait_for_timeout(5000)
                print(f"[TwitterClient] ✅ Tweet posted successfully: {text[:60]}...")
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
        with sync_playwright() as p:
            context, browser = self._get_context_and_browser(p)
            page = context.pages[0] if context.pages else context.new_page()
            try:
                print(f"[TwitterClient] Opening tweet for reply: {tweet_url}")
                page.goto(tweet_url, timeout=35000)
                
                # Wait for reply textarea
                reply_box = page.locator('[data-testid="tweetTextarea_0"], div[role="textbox"]').first
                reply_box.wait_for(state="visible", timeout=15000)
                self._human_type(reply_box, reply_text)

                reply_btn = page.locator('[data-testid="tweetButtonInline"], [data-testid="tweetButton"]').first
                time.sleep(random.uniform(0.8, 1.8))
                reply_btn.click()
                
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

    def get_latest_tweet_from_account(self, username: str) -> dict:
        """Fetches the latest tweet from a target viral account to snipe."""
        with sync_playwright() as p:
            context, browser = self._get_context_and_browser(p)
            page = context.pages[0] if context.pages else context.new_page()
            try:
                profile_url = f"https://x.com/{username}"
                page.goto(profile_url, timeout=35000)
                page.wait_for_selector('article[data-testid="tweet"]', timeout=15000)
                
                first_tweet = page.locator('article[data-testid="tweet"]').first
                tweet_text_el = first_tweet.locator('[data-testid="tweetText"]')
                tweet_text = tweet_text_el.inner_text() if tweet_text_el.is_visible() else ""
                
                # Extract tweet link
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
