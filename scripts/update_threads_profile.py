from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
avatar_img = BASE_DIR / "assets" / "neubench_avatar.jpg"

bio_text = "Real-time AI benchmarks & LLM evaluations across 260+ models. 📊 App: https://app.neubench.workers.dev • 𝕏: @GWorld34864 • 🦋 Bluesky: @neubench.bsky.social"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context("threads_session", headless=False, channel="chrome")
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.threads.net/@neubench", wait_until="domcontentloaded", timeout=40000)
    page.wait_for_timeout(4000)

    # 1. Click Edit profile
    edit_btn = page.get_by_text("Edit profile", exact=True).first
    if edit_btn.is_visible():
        edit_btn.click()
        page.wait_for_timeout(2000)

        # 2. Upload Avatar
        if avatar_img.exists():
            file_input = page.locator('input[type="file"]').first
            if file_input:
                print("Uploading avatar to Threads...")
                file_input.set_input_files(str(avatar_img.resolve()))
                page.wait_for_timeout(3000)

        # 3. Update Bio
        print("Opening Bio editor...")
        bio_btn = page.locator("div[role='button']:has-text('Bio')").first
        if bio_btn.is_visible():
            bio_btn.click()
            page.wait_for_timeout(1500)
            
            top_dialog = page.locator("div[role='dialog']").last
            textarea = top_dialog.locator("textarea").first
            if textarea.is_visible():
                print("Filling bio in top dialog...")
                textarea.click()
                textarea.fill(bio_text)
                page.wait_for_timeout(1000)
                
                # Click Done in Top Dialog
                done_bio = top_dialog.get_by_text("Done", exact=True).last
                print("Done Bio visible:", done_bio.is_visible())
                done_bio.click(force=True)
                page.wait_for_timeout(2000)

        # 4. Update Link
        print("Opening Link editor...")
        link_btn = page.locator("div[role='button']:has-text('Links')").first
        if link_btn.is_visible():
            link_btn.click()
            page.wait_for_timeout(1500)
            
            top_dialog = page.locator("div[role='dialog']").last
            link_input = top_dialog.locator('input[type="text"]').first
            if not link_input.is_visible():
                link_input = top_dialog.locator('input:not([type="checkbox"])').first
                
            if link_input.is_visible():
                print("Filling website link in top dialog...")
                link_input.click()
                link_input.fill("https://app.neubench.workers.dev")
                page.wait_for_timeout(1000)
                
                done_link = top_dialog.get_by_text("Done", exact=True).last
                done_link.click(force=True)
                page.wait_for_timeout(2000)

        # 5. Final Save on main modal
        print("Saving main Edit Profile modal...")
        main_dialog = page.locator("div[role='dialog']").first
        final_done = main_dialog.get_by_text("Done", exact=True).first
        if final_done.is_visible():
            final_done.click(force=True)
            page.wait_for_timeout(5000)

    page.goto("https://www.threads.net/@neubench", wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    page.screenshot(path="threads_updated_profile.png")
    print("✅ Threads profile update completed!")
    
    ctx.close()
