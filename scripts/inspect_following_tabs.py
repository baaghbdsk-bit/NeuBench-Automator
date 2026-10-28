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
        page.goto("https://x.com/GWorld34864/following", wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(4000)

        print("Current URL:", page.url)

        # Check tabs
        tabs = page.locator('[role="tab"]')
        print(f"Tabs count: {tabs.count()}")
        for t in range(tabs.count()):
            print(f"  Tab {t+1}: {tabs.nth(t).inner_text().strip()}")

        # Check user cells
        cells = page.locator('[data-testid="UserCell"]')
        print(f"Cells count: {cells.count()}")
        for i in range(min(cells.count(), 10)):
            print(f"  Cell {i+1}: {cells.nth(i).inner_text().replace(chr(10), ' | ')[:120]}")

    finally:
        ctx.close()

