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

def inspect_details():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(config.USER_DATA_DIR),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            print("\n=== 1. Checking Posts & Replies (with_replies) ===")
            page.goto("https://x.com/GWorld34864/with_replies", wait_until="domcontentloaded", timeout=35000)
            page.wait_for_timeout(5000)

            # Scroll once to trigger dynamic load
            page.mouse.wheel(0, 800)
            page.wait_for_timeout(2000)

            articles = page.locator('article[data-testid="tweet"]')
            count = articles.count()
            print(f"Total visible items in with_replies: {count}")
            for i in range(min(count, 10)):
                art = articles.nth(i)
                text = art.inner_text().replace("\n", " -- ")[:140]
                print(f"  [{i+1}] {text}")

            print("\n=== 2. Checking Following List (First 20 accounts) ===")
            page.goto("https://x.com/GWorld34864/following", wait_until="domcontentloaded", timeout=35000)
            page.wait_for_timeout(5000)

            user_cells = page.locator('[data-testid="UserCell"]')
            cell_count = user_cells.count()
            print(f"Total visible user cells: {cell_count}")
            for i in range(min(cell_count, 20)):
                cell = user_cells.nth(i)
                text = cell.inner_text().replace("\n", " | ")
                print(f"  ({i+1}) {text}")

        finally:
            ctx.close()

if __name__ == "__main__":
    inspect_details()

