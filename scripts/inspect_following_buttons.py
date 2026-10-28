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
        page.wait_for_timeout(3000)

        cells = page.locator('[data-testid="UserCell"]')
        print(f"Total cells: {cells.count()}")
        for i in range(min(cells.count(), 10)):
            cell = cells.nth(i)
            # Find handle
            link = cell.locator('a[href^="/"]').first
            href = link.get_attribute("href") or ""
            handle = href.strip("/").split("/")[0]

            # Find buttons
            buttons = cell.locator("button")
            btn_texts = [buttons.nth(b).inner_text().strip() for b in range(buttons.count())]
            print(f"Cell {i+1}: @{handle} -> Buttons: {btn_texts}")

    finally:
        ctx.close()

