import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from playwright.sync_api import sync_playwright

avatar_img = Path("assets/neubench_avatar.jpg").resolve()
threads_bio = "Real-time AI evals | Follow: 𝕏 @GWorld34864 | 🦋 Bluesky @neubench | 💼 in/vivek-gupta-b6b2951b2 | 👽 reddit u/Express-Cucumber-478"
print(f"Threads bio length: {len(threads_bio)} chars")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context("threads_session", headless=True)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.threads.net/@neubench", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    edit_btn = page.get_by_text("Edit profile", exact=True).first
    print("Edit profile button visible:", edit_btn.is_visible())
    if edit_btn.is_visible():
        edit_btn.click()
        page.wait_for_timeout(2000)

        # 1. Avatar
        file_input = page.locator('input[type="file"]').first
        if file_input.count():
            print("Setting avatar image...")
            file_input.set_input_files(str(avatar_img))
            page.wait_for_timeout(3000)

        # 2. Bio
        bio_btn = page.locator("div[role='button']:has-text('Bio')").first
        if bio_btn.is_visible():
            bio_btn.click()
            page.wait_for_timeout(1500)
            top_dialog = page.locator("div[role='dialog']").last
            ta = top_dialog.locator("textarea").first
            if ta.is_visible():
                ta.click()
                ta.fill(threads_bio)
                page.wait_for_timeout(1000)
                done_bio = top_dialog.get_by_text("Done", exact=True).last
                done_bio.click(force=True)
                page.wait_for_timeout(2000)
                print("Bio updated!")

        # 3. Link
        link_btn = page.locator("div[role='button']:has-text('Links')").first
        if link_btn.is_visible():
            link_btn.click()
            page.wait_for_timeout(1500)
            top_dialog = page.locator("div[role='dialog']").last
            inp = top_dialog.locator('input[type="text"]').first
            if not inp.is_visible():
                inp = top_dialog.locator('input:not([type="checkbox"])').first
            if inp.is_visible():
                inp.click()
                inp.fill("https://neubench.netlify.app")
                page.wait_for_timeout(1000)
                done_link = top_dialog.get_by_text("Done", exact=True).last
                done_link.click(force=True)
                page.wait_for_timeout(2000)
                print("Link updated!")

        # 4. Save Main Dialog
        main_dialog = page.locator("div[role='dialog']").first
        final_done = main_dialog.get_by_text("Done", exact=True).first
        if final_done.is_visible():
            final_done.click(force=True)
            page.wait_for_timeout(5000)
            print("Main profile saved!")

    page.goto("https://www.threads.net/@neubench", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    page.screenshot(path="threads_verified_live.png")
    print("Verified screenshot saved to threads_verified_live.png")
    ctx.close()
