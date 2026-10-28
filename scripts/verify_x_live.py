import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from playwright.sync_api import sync_playwright
import config

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(str(config.USER_DATA_DIR), headless=True, channel="chrome")
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://x.com/GWorld34864", timeout=30000)
    page.wait_for_timeout(4000)
    page.screenshot(path="x_final_verified_live.png")
    
    # Locate UserDescription
    bio_el = page.locator('div[data-testid="UserDescription"]').first
    header_el = page.locator('div[data-testid="UserProfileHeader_Items"]').first
    name_el = page.locator('div[data-testid="UserName"]').first
    
    print("=== 𝕏 LIVE PROFILE VERIFIED ===")
    if name_el.is_visible():
        print("Name:", name_el.inner_text().replace("\n", " "))
    if bio_el.is_visible():
        print("Bio:", bio_el.inner_text())
    if header_el.is_visible():
        print("Links / Location:", header_el.inner_text().replace("\n", " | "))

    ctx.close()
