import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import config

avatar_img = BASE_DIR / "assets" / "neubench_avatar.jpg"
banner_img = BASE_DIR / "assets" / "neubench_twitter_banner.jpg"

# 157 chars - exactly fits X's 160 char limit
x_bio = "Real-time AI evals (neubench.netlify.app) | Follow: 🦋 bsky: @neubench | 🧵 threads: @neubench | 💼 in/vishnu-gupta-b6b2951b2 | 👽 reddit: u/Express-Cucumber-478"
print(f"X Bio length: {len(x_bio)} / 160 characters")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(config.USER_DATA_DIR),
        headless=True,
        viewport={"width": 1280, "height": 850},
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    page.goto("https://x.com/home", timeout=35000)
    page.wait_for_timeout(3000)

    # Go to profile
    profile_link = page.locator('a[data-testid="AppTabBar_Profile_Link"]').first
    if profile_link.is_visible():
        profile_link.click()
    else:
        page.goto("https://x.com/GWorld34864", timeout=35000)
    page.wait_for_timeout(3000)

    # Click Edit profile
    edit_btn = page.locator('[data-testid="editProfileButton"]').first
    if edit_btn.is_visible():
        edit_btn.click()
        page.wait_for_timeout(2000)

    # Name
    name_el = page.locator('input[name="displayName"]').first
    if name_el.is_visible():
        name_el.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        name_el.type("NeuBench", delay=40)
        page.wait_for_timeout(300)

    # Bio
    bio_el = page.locator('textarea[name="description"]').first
    if bio_el.is_visible():
        bio_el.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        bio_el.type(x_bio, delay=20)
        page.wait_for_timeout(300)
        print("Filled Bio!")

    # Location
    loc_el = page.locator('input[name="location"]').first
    if loc_el.is_visible():
        loc_el.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        loc_el.type("Global • AI Benchmarks", delay=30)
        page.wait_for_timeout(300)

    # Website URL
    url_el = page.locator('input[name="url"]').first
    if url_el.is_visible():
        url_el.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        url_el.type("https://neubench.netlify.app", delay=30)
        page.wait_for_timeout(300)
        print("Filled Website URL: https://neubench.netlify.app")

    # Banner
    if banner_img.exists():
        file_inputs = page.locator('input[type="file"]').all()
        if len(file_inputs) >= 1:
            file_inputs[0].set_input_files(str(banner_img.resolve()))
            page.wait_for_timeout(2500)
            apply_btn = page.locator('[data-testid="applyButton"]').first
            if apply_btn.is_visible():
                apply_btn.click()
                page.wait_for_timeout(2500)

    # Avatar
    if avatar_img.exists():
        file_inputs = page.locator('input[type="file"]').all()
        avatar_input = file_inputs[1] if len(file_inputs) >= 2 else file_inputs[0]
        avatar_input.set_input_files(str(avatar_img.resolve()))
        page.wait_for_timeout(2500)
        apply_btn = page.locator('[data-testid="applyButton"]').first
        if apply_btn.is_visible():
            apply_btn.click()
            page.wait_for_timeout(2500)

    # Save
    save_btn = page.locator('[data-testid="Profile_Save_Button"]').first
    if save_btn.is_visible() and save_btn.is_enabled():
        save_btn.click()
        page.wait_for_timeout(5000)
        print("✅ 𝕏 Profile Saved!")

    page.screenshot(path="x_profile_complete.png")
    ctx.close()
