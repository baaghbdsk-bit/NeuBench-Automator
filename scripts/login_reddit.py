"""Interactive Reddit login and portable cookie export."""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
SESSION_DIR = BASE_DIR / "reddit_session"
COOKIE_FILE = SESSION_DIR / "cookies.json"


def login_reddit() -> bool:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        try:
            page.goto("https://www.reddit.com/login/", wait_until="domcontentloaded", timeout=45000)
            input("Log in to Reddit, reach your feed, then press ENTER here...\n")
            page.goto("https://www.reddit.com/", wait_until="domcontentloaded", timeout=30000)
            if "login" in page.url.lower():
                print("Reddit login was not detected.")
                return False
            COOKIE_FILE.write_text(json.dumps(context.cookies(), indent=2), encoding="utf-8")
            print(f"Reddit session saved to {COOKIE_FILE}")
            return True
        finally:
            context.close()


if __name__ == "__main__":
    sys.exit(0 if login_reddit() else 1)
