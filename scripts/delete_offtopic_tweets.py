import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from playwright.sync_api import sync_playwright
import config

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Keywords of off-topic test tweets to delete
TEST_KEYWORDS = [
    "real madrid",
    "nba league pass",
    "donovan mitchell",
    "cleaning fee",
    "green lights are just for moral support"
]

def clean_test_tweets():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(config.USER_DATA_DIR),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            print(">>> Navigating to https://x.com/GWorld34864 ...")
            page.goto("https://x.com/GWorld34864", wait_until="domcontentloaded", timeout=35000)
            page.wait_for_timeout(4000)

            deleted = 0
            for loop in range(10):
                articles = page.locator('article[data-testid="tweet"]')
                count = articles.count()
                found_target = False

                for i in range(count):
                    try:
                        art = articles.nth(i)
                        txt = art.inner_text().lower()
                        
                        if any(kw in txt for kw in TEST_KEYWORDS):
                            print(f"\nTarget tweet found: {txt[:100]}...")
                            caret = art.locator('[data-testid="caret"]').first
                            if caret.is_visible():
                                caret.click()
                                page.wait_for_timeout(1000)

                                del_btn = page.locator('[role="menuitem"]:has-text("Delete")').first
                                if del_btn.is_visible():
                                    del_btn.click()
                                    page.wait_for_timeout(1000)

                                    confirm = page.locator('[data-testid="confirmationSheetConfirm"]').first
                                    if confirm.is_visible():
                                        confirm.click()
                                        deleted += 1
                                        print(f"  🗑️ Deleted #{deleted} successfully!")
                                        page.wait_for_timeout(2500)
                                        found_target = True
                                        break
                                else:
                                    print("  Delete option not found in dropdown (might be someone else's retweet).")
                                    # Click outside to close dropdown
                                    page.mouse.click(10, 10)
                    except Exception as e:
                        print(f"  Error on item {i}: {e}")

                if not found_target:
                    # Scroll down to see if older ones are below
                    page.mouse.wheel(0, 1200)
                    page.wait_for_timeout(2500)

            print(f"\nFinished tweet cleanup! Total deleted: {deleted}")

        finally:
            ctx.close()

if __name__ == "__main__":
    clean_test_tweets()

