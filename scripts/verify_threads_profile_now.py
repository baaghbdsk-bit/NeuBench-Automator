import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context("threads_session", headless=True)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.threads.net/@neubench", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # Print first 20 lines of text from main
    lines = [l.strip() for l in page.locator("main").inner_text().split("\n") if l.strip()]
    for l in lines[:15]:
        print("Threads text:", l)

    # Check the profile picture img
    imgs = page.locator("main img").all()
    for idx, i in enumerate(imgs[:5]):
        print(f"Threads img {idx}:", i.get_attribute("src")[:90], "alt:", i.get_attribute("alt"))

    ctx.close()
