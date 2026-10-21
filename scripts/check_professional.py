import sys
from pathlib import Path
import time

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def enable_category_on_profile(target_category: str = "Science & Technology"):
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(config.USER_DATA_DIR), headless=True)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://x.com/GWorld34864", timeout=30000)
        page.wait_for_timeout(3000)
        
        # Click edit profile
        edit_btn = page.locator('[data-testid="editProfileButton"]').first
        if edit_btn.is_visible():
            edit_btn.click()
            page.wait_for_timeout(2000)
            
            # Click 'Edit professional profile'
            pro_btn = page.locator('text="Edit professional profile"').first
            if pro_btn.is_visible():
                print("Clicking 'Edit professional profile'...")
                pro_btn.click()
                page.wait_for_timeout(3000)
                
                print("--- PROFESSIONAL SETTINGS TEXT ---")
                print(page.locator('main, div[role="dialog"]').first.inner_text())
                print("-----------------------------------")
                page.screenshot(path="pro_settings.png")
        ctx.close()

if __name__ == "__main__":
    enable_category_on_profile()

