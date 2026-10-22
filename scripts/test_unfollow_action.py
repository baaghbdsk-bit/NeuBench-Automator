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
        page.goto("https://x.com/ARanganathan72", wait_until="domcontentloaded", timeout=25000)
        page.wait_for_timeout(2500)

        unfollow_btn = page.locator('button[data-testid$="-unfollow"]').first
        if unfollow_btn.is_visible():
            print("Clicking unfollow button...")
            unfollow_btn.click()
            page.wait_for_timeout(1000)

            confirm = page.locator('[data-testid="confirmationSheetConfirm"]').first
            if confirm.is_visible():
                print("Clicking confirm button...")
                confirm.click()
                page.wait_for_timeout(2000)
                print("Successfully unfollowed ARanganathan72!")
            else:
                print("Confirm button not found!")
        else:
            print("Unfollow button not visible!")

    finally:
        ctx.close()
