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
        page.goto("https://x.com/AndrewYNg", wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(3000)

        btns = page.locator('button')
        print(f"Total buttons on AndrewYNg profile: {btns.count()}")
        for i in range(btns.count()):
            btn = btns.nth(i)
            tid = btn.get_attribute("data-testid") or ""
            txt = btn.inner_text().strip()
            print(f"  Button: txt='{txt}', testid='{tid}'")

    finally:
        ctx.close()

