import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from playwright.sync_api import sync_playwright
import config

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(config.USER_DATA_DIR),
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    try:
        page.goto("https://x.com/GWorld34864", wait_until="domcontentloaded", timeout=35000)
        page.wait_for_timeout(4000)

        for s in range(3):
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(2000)

        # Look for tweet text or carets
        carets = page.locator('[data-testid="caret"]')
        print(f"Total carets (tweet menu buttons): {carets.count()}")

        articles = page.locator('article')
        print(f"Total article tags: {articles.count()}")
        for i in range(min(articles.count(), 10)):
            print(f"Article {i+1}: {articles.nth(i).inner_text().replace(chr(10), ' | ')[:140]}")

    finally:
        ctx.close()

