import sys
import time
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from playwright.sync_api import sync_playwright
import config

def update_x_profile(name: str = None, bio: str = None, location: str = None, avatar_path: str = None) -> bool:
    print(f"\n[Profile Updater] Starting profile update...")
    if name: print(f"  Name: {name}")
    if bio: print(f"  Bio: {bio}")
    if location: print(f"  Location: {location}")
    if avatar_path: print(f"  Avatar: {avatar_path}\n")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(config.USER_DATA_DIR),
            headless=True,
            viewport={"width": 1280, "height": 850},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            print("[Profile Updater] Navigating to X Home...")
            page.goto("https://x.com/home", timeout=35000)
            page.wait_for_timeout(3000)

            print("[Profile Updater] Opening Profile...")
            profile_link = page.locator('a[data-testid="AppTabBar_Profile_Link"]').first
            if profile_link.is_visible():
                profile_link.click()
            else:
                page.goto("https://x.com/settings/profile", timeout=35000)
            
            page.wait_for_timeout(3000)
            print(f"[Profile Updater] Current URL: {page.url}")

            # Click Edit Profile
            edit_btn = page.locator('[data-testid="editProfileButton"]').first
            if edit_btn.is_visible():
                print("[Profile Updater] Clicking 'Edit profile' button...")
                edit_btn.click()
                page.wait_for_timeout(2000)

            # Wait for modal
            page.wait_for_selector('input[name="displayName"]', timeout=15000)

            # Upload Avatar if provided
            if avatar_path and Path(avatar_path).exists():
                print(f"[Profile Updater] Uploading avatar image: {avatar_path}...")
                file_inputs = page.locator('input[type="file"]').all()
                if len(file_inputs) >= 2:
                    # Index 1 is the circular avatar input
                    avatar_input = file_inputs[1]
                elif len(file_inputs) == 1:
                    avatar_input = file_inputs[0]
                else:
                    avatar_input = None

                if avatar_input:
                    avatar_input.set_input_files(str(avatar_path))
                    page.wait_for_timeout(3000)
                    
                    # Check for crop / apply button
                    apply_btn = page.locator('[data-testid="applyButton"]').first
                    if apply_btn.is_visible():
                        print("[Profile Updater] Applying avatar crop...")
                        apply_btn.click()
                        page.wait_for_timeout(3000)
                    print("[Profile Updater] ✅ Avatar uploaded successfully!")
                else:
                    print("[Profile Updater] ⚠️ Could not find avatar file input.")

            # Update Name
            if name:
                name_el = page.locator('input[name="displayName"]').first
                name_el.click()
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.wait_for_timeout(300)
                name_el.type(name, delay=50)
                page.wait_for_timeout(300)
                print(f"[Profile Updater] Set Name to: {name}")

            # Update Bio
            if bio:
                bio_el = page.locator('textarea[name="description"]').first
                if bio_el.is_visible():
                    bio_el.click()
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    page.wait_for_timeout(300)
                    bio_el.type(bio, delay=30)
                    page.wait_for_timeout(300)
                    print(f"[Profile Updater] Set Bio to: {bio[:40]}...")

            # Update Location
            if location:
                loc_el = page.locator('input[name="location"]').first
                if loc_el.is_visible():
                    loc_el.click()
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    page.wait_for_timeout(300)
                    loc_el.type(location, delay=40)
                    page.wait_for_timeout(300)
                    print(f"[Profile Updater] Set Location to: {location}")

            # Save
            save_btn = page.locator('[data-testid="Profile_Save_Button"]').first
            if save_btn.is_visible() and save_btn.is_enabled():
                print("[Profile Updater] Clicking Save button...")
                save_btn.click()
                page.wait_for_timeout(5000)
                
                modal_open = page.locator('input[name="displayName"]').is_visible()
                if not modal_open:
                    print("[Profile Updater] ✅ Profile and Avatar saved successfully!")
                    screenshot_path = BASE_DIR / "profile_updated.png"
                    page.screenshot(path=str(screenshot_path))
                    print(f"[Profile Updater] Updated screenshot: {screenshot_path}")
                    return True
                else:
                    print("[Profile Updater] ⚠️ Modal still open after clicking save.")
                    return False
            else:
                print("[Profile Updater] ❌ Save button not clickable.")
                return False

        except Exception as e:
            print(f"[Profile Updater] ❌ Error: {e}")
            screenshot_path = BASE_DIR / "profile_error.png"
            page.screenshot(path=str(screenshot_path))
            return False
        finally:
            ctx.close()

if __name__ == "__main__":
    avatar_file = BASE_DIR / "avatar.jpg"
    update_x_profile(
        name="vishnu rot",
        bio="Tech, markets & the absurd reality of modern work. Calling out what everyone thinks but won't tweet. | Building in public.",
        location="Bengaluru / Earth",
        avatar_path=str(avatar_file) if avatar_file.exists() else None
    )
