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

def toggle_category_visibility():
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
                pro_btn.click()
                page.wait_for_timeout(3000)
                
                # Find switch / toggle for 'Show category on profile'
                switch = page.locator('input[type="checkbox"], [role="switch"]').first
                if switch.is_visible():
                    is_checked = switch.is_checked() if switch.evaluate('el => el.tagName === "INPUT"') else (switch.get_attribute('aria-checked') == 'true')
                    print(f"Current toggle state: {is_checked}")
                    
                    if not is_checked:
                        print("Turning 'Show category on profile' ON...")
                        switch.click()
                        page.wait_for_timeout(1000)
                    else:
                        print("'Show category on profile' is already ON.")
                
                # Check for Save or back button
                save_btn = page.locator('button:has-text("Save"), [data-testid="Profile_Save_Button"]').first
                if save_btn.is_visible() and save_btn.is_enabled():
                    print("Clicking Save in professional profile...")
                    save_btn.click()
                    page.wait_for_timeout(3000)
                
                # Take screenshot of final profile
                page.goto("https://x.com/GWorld34864", timeout=30000)
                page.wait_for_timeout(3000)
                page.screenshot(path="profile_final.png")
                print("Final profile screenshot saved to: profile_final.png")
        ctx.close()

if __name__ == "__main__":
    toggle_category_visibility()

