import os
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from playwright.sync_api import sync_playwright

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config

def login_and_save_session():
    """
    Opens a real browser window for the user to log into X once.
    Saves the full session profile so the bot can run headlessly or automatically.
    """
    os.makedirs(config.USER_DATA_DIR, exist_ok=True)
    
    print("\n" + "="*60)
    print("🚀 X-Post-Automater: 1-Time Session Setup")
    print("="*60)
    print("A browser window is about to open.")
    print("1. Log in to your X (Twitter) account.")
    print("2. Complete any 2FA or verification if prompted.")
    print("3. Wait until you see your normal X Home Feed.")
    print("4. Return here and press ENTER to save your session.")
    print("="*60 + "\n")

    with sync_playwright() as p:
        # Launch persistent context so Chrome stores local storage & cookies
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(config.USER_DATA_DIR),
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://x.com/login")
        
        input("\n👉 Press ENTER here in this console AFTER you have successfully logged in...")
        
        # Save storage state (cookies + local storage)
        context.storage_state(path=str(config.COOKIES_FILE))
        print(f"\n✅ Session successfully saved to: {config.COOKIES_FILE}")
        print("Your automator is now ready to post without needing login credentials again!\n")
        
        context.close()

if __name__ == "__main__":
    login_and_save_session()
