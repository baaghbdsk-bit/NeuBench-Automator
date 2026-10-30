import sys
import os
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SESSION_DIR = Path(__file__).resolve().parent.parent / "pinterest_session"
SESSION_DIR.mkdir(parents=True, exist_ok=True)
COOKIES_FILE = SESSION_DIR / "cookies.json"

def login_pinterest():
    print("=" * 60)
    print("📌 Pinterest Interactive Session Login")
    print("=" * 60)
    print("1. A Chromium browser window will open at pinterest.com/login.")
    print("2. Log into your Pinterest account.")
    print("3. Once logged in and on your Pinterest homefeed/profile, press ENTER in this terminal.")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

        page = context.new_page()
        page.goto("https://www.pinterest.com/login/")

        input("\n>>> Press ENTER here AFTER you have successfully logged in on Pinterest... <<<")

        cookies = context.cookies()
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)

        print(f"\n✅ Pinterest cookies successfully saved to: {COOKIES_FILE}")
        browser.close()

if __name__ == "__main__":
    login_pinterest()
