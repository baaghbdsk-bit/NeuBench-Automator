import sys
import time
import random
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

def inspect_profile():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(config.USER_DATA_DIR),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            print(">>> Navigating to profile: https://x.com/GWorld34864 ...")
            page.goto("https://x.com/GWorld34864", wait_until="domcontentloaded", timeout=35000)
            page.wait_for_timeout(4000)

            # Check tweets
            articles = page.locator('article[data-testid="tweet"]')
            count = articles.count()
            print(f">>> Found {count} visible tweets in current view.")

            tweets = []
            for i in range(min(count, 15)):
                art = articles.nth(i)
                text = art.inner_text().replace("\n", " | ")[:120]
                tweets.append(text)
                print(f"  [{i+1}] {text}")

            # Check following count
            following_link = page.locator('a[href$="/following"]').first
            followers_link = page.locator('a[href$="/verified_followers"]').first
            
            f_ing = following_link.inner_text().strip() if following_link.is_visible() else "unknown"
            f_ers = followers_link.inner_text().strip() if followers_link.is_visible() else "unknown"
            print(f"\n>>> Following: {f_ing} | Followers: {f_ers}")

            return tweets
        finally:
            ctx.close()

if __name__ == "__main__":
    inspect_profile()

