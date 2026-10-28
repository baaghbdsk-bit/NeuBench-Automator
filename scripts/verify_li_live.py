import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context("linkedin_session", headless=True)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.linkedin.com/in/me/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    page.screenshot(path="linkedin_live_check.png")
    print("Screenshot saved to linkedin_live_check.png")
    
    # Check all buttons with background or edit
    for b in page.locator("button[aria-label]").all():
        aria = b.get_attribute("aria-label") or ""
        if any(w in aria.lower() for w in ["background", "cover", "photo", "image", "edit"]):
            print("Found button:", aria)

    # Check text
    print("Profile Headline snippet:")
    text = page.locator("main section").first.inner_text()
    print("\n".join(text.split("\n")[:10]))

    ctx.close()
