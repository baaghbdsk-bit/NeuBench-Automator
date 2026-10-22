import sys
import time
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
        page.wait_for_timeout(3500)

        follow_btn = page.locator('button[data-testid$="-follow"]').first
        print("Follow button visible:", follow_btn.is_visible())
        if follow_btn.is_visible():
            follow_btn.click()
            page.wait_for_timeout(2500)
            print("Successfully clicked follow on AndrewYNg!")

            # Verify it now says Following
            unfollow_btn = page.locator('button[data-testid$="-unfollow"]').first
            print("Now following AndrewYNg:", unfollow_btn.is_visible())

    finally:
        ctx.close()
