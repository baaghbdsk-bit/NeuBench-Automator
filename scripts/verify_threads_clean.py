import sys
sys.stdout.reconfigure(encoding="utf-8")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context("threads_session", headless=True)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.threads.net/@neubench", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    for l in page.locator("main header, header").inner_text().split("\n"):
        if l.strip():
            print("Threads Header:", l.strip())
    img = page.locator("header img, main header img").first
    if img.count():
        print("Threads Avatar Img URL:", img.get_attribute("src")[:90])
    ctx.close()
