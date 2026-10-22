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
        page.goto("https://x.com/GWorld34864", wait_until="networkidle", timeout=35000)
        page.wait_for_timeout(3000)

        # Let's inspect all articles or cellInnerDiv
        cells = page.locator('[data-testid="cellInnerDiv"]')
        print(f"cellInnerDiv count: {cells.count()}")
        for i in range(min(cells.count(), 10)):
            txt = cells.nth(i).inner_text().replace("\n", " | ")
            if txt.strip():
                print(f"Cell {i+1}: {txt[:120]}")

    finally:
        ctx.close()
