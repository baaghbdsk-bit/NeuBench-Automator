import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from playwright.sync_api import sync_playwright

avatar_img = Path("assets/neubench_avatar.jpg").resolve()
banner_img = Path("assets/neubench_twitter_banner.jpg").resolve()
reddit_bio = "Real-time AI evals across 260+ models (https://app.neubench.workers.dev) | Follow: 𝕏 @GWorld34864 | 🦋 Bluesky @neubench | 🧵 Threads @neubench | 💼 LinkedIn in/vishnu-gupta-b6b2951b2"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context("reddit_session", headless=True)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.reddit.com/settings/profile", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    # 1. Display name
    display_name_el = page.locator('input[name="displayName"], input[aria-label*="Display name"]').first
    if not display_name_el.is_visible():
        display_name_el = page.locator('input[placeholder*="Display name"], input[id*="display-name"]').first
    if display_name_el.is_visible():
        display_name_el.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        display_name_el.fill("NeuBench")
        page.wait_for_timeout(500)
        print("Set Display Name: NeuBench")

    # 2. About
    about_el = page.locator('textarea[name="about"], textarea[aria-label*="About"], textarea[id*="about"]').first
    if not about_el.is_visible():
        about_el = page.locator('textarea').first
    if about_el.is_visible():
        about_el.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        about_el.fill(reddit_bio)
        page.wait_for_timeout(500)
        print("Set Reddit About / Bio")

    # 3. Avatar and Banner
    file_inputs = page.locator('input[type="file"]').all()
    print(f"Reddit file inputs found: {len(file_inputs)}")
    if len(file_inputs) >= 1 and avatar_img.exists():
        file_inputs[0].set_input_files(str(avatar_img))
        page.wait_for_timeout(3000)
        print("Uploaded Reddit Avatar!")
    if len(file_inputs) >= 2 and banner_img.exists():
        file_inputs[1].set_input_files(str(banner_img))
        page.wait_for_timeout(3000)
        print("Uploaded Reddit Banner!")

    # Check for save button
    for b in page.locator('button:has-text("Save"), button:has-text("Save changes")').all():
        if b.is_visible():
            b.click()
            print("Clicked Save on Reddit settings!")
            page.wait_for_timeout(2000)

    page.wait_for_timeout(3000)
    page.goto("https://www.reddit.com/user/Express-Cucumber-478/", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    page.screenshot(path="reddit_verified_live.png")
    print("Reddit verified screenshot saved to reddit_verified_live.png")
    ctx.close()
