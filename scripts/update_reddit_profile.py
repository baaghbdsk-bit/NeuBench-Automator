import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
avatar_img = BASE_DIR / "assets" / "neubench_avatar.jpg"
banner_img = BASE_DIR / "assets" / "neubench_twitter_banner.jpg"

bio_text = "Real-time AI benchmarks & LLM evaluations across 260+ models. App: https://app.neubench.workers.dev | 𝕏: @GWorld34864 | Threads: @neubench"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context("reddit_session", headless=False, channel="chrome")
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.reddit.com/settings/profile", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4000)
    page.screenshot(path="reddit_settings_page.png")

    print("Reddit Settings URL:", page.url)
    print("Reddit Settings Title:", page.title())

    # 1. Display name
    display_name_el = page.locator('input[name="displayName"], input[aria-label*="Display name"]').first
    if not display_name_el.is_visible():
        display_name_el = page.locator('input[placeholder*="Display name"], input[id*="display-name"]').first
    
    print("Display name field visible:", display_name_el.is_visible() if display_name_el else False)
    if display_name_el and display_name_el.is_visible():
        display_name_el.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        display_name_el.fill("NeuBench")
        page.wait_for_timeout(500)
        print("Filled Display Name: NeuBench")

    # 2. About / Bio description
    about_el = page.locator('textarea[name="about"], textarea[aria-label*="About"], textarea[id*="about"]').first
    if not about_el.is_visible():
        about_el = page.locator('textarea').first
        
    print("About field visible:", about_el.is_visible() if about_el else False)
    if about_el and about_el.is_visible():
        about_el.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        about_el.fill(bio_text)
        page.wait_for_timeout(500)
        print("Filled About / Bio")

    # 3. Avatar Upload
    file_inputs = page.locator('input[type="file"]').all()
    print("File inputs found:", len(file_inputs))
    if file_inputs and avatar_img.exists():
        print("Uploading Avatar to Reddit...")
        file_inputs[0].set_input_files(str(avatar_img.resolve()))
        page.wait_for_timeout(4000)

    # 4. Save if save button exists (Reddit auto-saves or has a save button)
    save_btns = page.locator('button:has-text("Save"), button:has-text("Save changes")').all()
    for b in save_btns:
        if b.is_visible():
            b.click()
            print("Clicked Save changes on Reddit!")
            page.wait_for_timeout(3000)

    page.wait_for_timeout(3000)
    page.goto("https://www.reddit.com/user/Express-Cucumber-478/", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    page.screenshot(path="reddit_profile_verified.png")
    print("✅ Reddit Profile Update Completed!")
    ctx.close()
