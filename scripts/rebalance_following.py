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

TO_FOLLOW = [
    "sama",
    "karpathy",
    "elonmusk",
    "narendramodi",
    "ylecun",
    "satyanadella",
    "demishassabis",
    "levelsio",
    "IndianTechGuide",
    "peakbengaluru"
]

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(config.USER_DATA_DIR),
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    try:
        # Step 1: Unfollow older accounts
        print("\n--- Step 1: Unfollowing Old / Unrelated Accounts ---")
        page.goto("https://x.com/GWorld34864/following", wait_until="domcontentloaded", timeout=35000)
        page.wait_for_timeout(3000)

        unfollowed_count = 0
        max_loops = 20

        for _ in range(max_loops):
            unfollow_btns = page.locator('button[data-testid$="-unfollow"]')
            count = unfollow_btns.count()
            if count == 0:
                print("No more accounts to unfollow.")
                break

            btn = unfollow_btns.first
            label = btn.get_attribute("aria-label") or "account"
            print(f"Unfollowing: {label}...")
            btn.click()
            page.wait_for_timeout(1000)

            confirm_btn = page.locator('[data-testid="confirmationSheetConfirm"]').first
            if confirm_btn.is_visible():
                confirm_btn.click()
                unfollowed_count += 1
                print(f"  Unfollowed #{unfollowed_count} successfully.")
                time.sleep(random.uniform(1.2, 2.0))
            else:
                print("  Confirmation button not visible, scrolling or breaking.")
                break

        print(f"Total old accounts unfollowed: {unfollowed_count}")

        # Step 2: Follow top AI & Tech leaders
        print("\n--- Step 2: Following Top AI & Tech Leaders ---")
        followed_count = 0
        for username in TO_FOLLOW:
            try:
                print(f"Visiting @{username}...")
                page.goto(f"https://x.com/{username}", wait_until="domcontentloaded", timeout=35000)
                page.wait_for_timeout(2500)

                # Check if already following
                unfollow_btn = page.locator('button[data-testid$="-unfollow"]').first
                if unfollow_btn.is_visible():
                    print(f"  Already following @{username}.")
                    continue

                # Click Follow button
                follow_btn = page.locator('button[data-testid$="-follow"]').first
                if follow_btn.is_visible():
                    follow_btn.click()
                    page.wait_for_timeout(2000)
                    followed_count += 1
                    print(f"  ✅ Followed @{username} successfully!")
                    time.sleep(random.uniform(1.5, 3.0))
                else:
                    print(f"  Follow button not found on @{username}.")

            except Exception as e:
                print(f"  Error on @{username}: {e}")

        print(f"\nCompleted! Total new leaders followed: {followed_count}")

    finally:
        ctx.close()

