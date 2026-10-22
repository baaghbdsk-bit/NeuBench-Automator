import sys
import time
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from playwright.sync_api import sync_playwright
import config

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def audit_following():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(config.USER_DATA_DIR),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            print(">>> Navigating to https://x.com/GWorld34864/following ...")
            page.goto("https://x.com/GWorld34864/following", wait_until="domcontentloaded", timeout=35000)
            page.wait_for_timeout(4000)

            following_data = []
            seen_handles = set()

            for scroll in range(12):
                cells = page.locator('[data-testid="UserCell"]')
                count = cells.count()
                for i in range(count):
                    try:
                        cell = cells.nth(i)
                        # Extract handle
                        link = cell.locator('a[href^="/"]').first
                        href = link.get_attribute("href") if link.is_visible() else ""
                        handle = href.strip("/").split("/")[0] if href else ""
                        
                        if handle and handle not in seen_handles and handle != "GWorld34864":
                            seen_handles.add(handle)
                            text = cell.inner_text().replace("\n", " | ")
                            following_data.append({"handle": handle, "preview": text[:120]})
                    except Exception:
                        pass
                
                page.mouse.wheel(0, 1500)
                page.wait_for_timeout(1500)

            print(f"\n>>> Total unique following accounts found: {len(following_data)}")
            for idx, item in enumerate(following_data):
                print(f"[{idx+1}] @{item['handle']} -> {item['preview']}")

            out_file = BASE_DIR / "following_audit.json"
            out_file.write_text(json.dumps(following_data, indent=2), encoding="utf-8")
            print(f"\nSaved audit to {out_file}")

        finally:
            ctx.close()

if __name__ == "__main__":
    audit_following()
