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

        # Check page text for tweets count or empty state
        body_text = page.locator("body").inner_text()
        print("Profile Page Snippet:")
        for line in body_text.splitlines():
            line = line.strip()
            if any(k in line.lower() for k in ["post", "tweet", "repl", "joined", "follow", "neubench", "empty"]):
                print(f"  {line}")

    finally:
        ctx.close()

