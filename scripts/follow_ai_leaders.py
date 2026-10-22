import sys
import time
import random
from pathlib import Path

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

AI_LEADERS = [
    "JeffDean",
    "AnthropicAI",
    "drjimfan",
    "svpino",
    "huggingface"
]

def follow_leaders():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(config.USER_DATA_DIR),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            print("==================================================")
            print("🚀 Following Top AI Leaders on X")
            print("==================================================")
            followed = 0
            for handle in AI_LEADERS:
                try:
                    print(f"Visiting https://x.com/{handle} ...")
                    page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(3500)

                    # Check if already following
                    unfollow_btn = page.locator('button[data-testid$="-unfollow"]').first
                    if unfollow_btn.is_visible():
                        print(f"  Already following @{handle}")
                        continue

                    follow_btn = page.locator('button[data-testid$="-follow"]').first
                    if follow_btn.is_visible():
                        follow_btn.click()
                        page.wait_for_timeout(2000)
                        followed += 1
                        print(f"  ✅ Successfully followed @{handle} (#{followed})!")
                        time.sleep(random.uniform(2.0, 3.5))
                    else:
                        print(f"  Follow button not visible on @{handle}")
                except Exception as e:
                    print(f"  Error on @{handle}: {e}")

            print(f"\n🎉 Completed! Total AI leaders followed in this run: {followed}")

        finally:
            ctx.close()

if __name__ == "__main__":
    follow_leaders()
