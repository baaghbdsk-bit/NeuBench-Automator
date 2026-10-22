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

UNRELATED_ACCOUNTS = {
    "rishibagree",
    "jaipurdialogues",
    "aranganathan72",
    "genbakshi_in",
    "ajeetbharti",
    "iamharshbeniwal",
    "klrajiv",
    "thenavroopsingh",
    "ajaykraina",
    "atsshow7",
    "we_indianin",
    "sirpareshrawal",
    "majorgauravarya",
    "aadiachint",
    "sanjay_dixit",
    "shambhav15",
    "iyervval",
    "sushantbsinha",
    "realsiff",
    "sudhanshutrived",
    "ashwiniupadhyay",
    "abhijitchavda",
    "ankitatiima",
    "data_ecosystem",
    "xuanzhenz",
    "eth_daily",
    "coinmarketcap",
    "bitlayerlabs",
    "cygnusfi",
    "lorenzoprotocol",
    "binancewallet",
    "plumenetwork"
}

AI_LEADERS_TO_FOLLOW = [
    "AndrewYNg",
    "JeffDean",
    "AnthropicAI",
    "drjimfan",
    "svpino",
    "huggingface"
]

def unfollow_and_rebalance():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(config.USER_DATA_DIR),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            print("==================================================")
            print("🚀 STEP 1: Unfollowing Unrelated Accounts from Following List")
            print("==================================================")
            page.goto("https://x.com/GWorld34864/following", wait_until="domcontentloaded", timeout=35000)
            page.wait_for_timeout(4000)

            unfollowed_count = 0
            unfollowed_handles = set()

            for loop in range(35):
                cells = page.locator('[data-testid="UserCell"]')
                count = cells.count()
                found_in_view = False

                for i in range(count):
                    try:
                        cell = cells.nth(i)
                        link = cell.locator('a[href^="/"]').first
                        href = link.get_attribute("href") or ""
                        handle = href.strip("/").split("/")[0].lower()

                        if handle in UNRELATED_ACCOUNTS and handle not in unfollowed_handles:
                            # Look for Following button
                            btn = cell.locator('button:has-text("Following"), button[data-testid$="-unfollow"]').first
                            if btn.is_visible():
                                print(f"Unfollowing @{handle}...")
                                btn.click()
                                page.wait_for_timeout(1000)

                                confirm = page.locator('[data-testid="confirmationSheetConfirm"]').first
                                if confirm.is_visible():
                                    confirm.click()
                                    unfollowed_count += 1
                                    unfollowed_handles.add(handle)
                                    print(f"  ❌ Unfollowed #{unfollowed_count}: @{handle}")
                                    page.wait_for_timeout(1800)
                                    found_in_view = True
                                    break
                    except Exception as e:
                        pass

                if not found_in_view:
                    # Scroll down to load more
                    page.mouse.wheel(0, 800)
                    page.wait_for_timeout(1500)

            print(f"\n✅ Total accounts unfollowed: {unfollowed_count}")

            print("\n==================================================")
            print("🚀 STEP 2: Following Top AI Leaders")
            print("==================================================")
            followed_count = 0
            for handle in AI_LEADERS_TO_FOLLOW:
                try:
                    print(f"Visiting @{handle}...")
                    page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(2500)

                    # Check if already following
                    unfollow_btn = page.locator('button[data-testid$="-unfollow"], button:has-text("Following")').first
                    if unfollow_btn.is_visible():
                        print(f"  Already following @{handle}")
                        continue

                    # Click follow
                    follow_btn = page.locator('button[data-testid$="-follow"], button:has-text("Follow")').first
                    if follow_btn.is_visible():
                        follow_btn.click()
                        followed_count += 1
                        print(f"  ➕ Followed @{handle} (#{followed_count})")
                        time.sleep(random.uniform(2.0, 3.5))
                    else:
                        print(f"  Follow button not found on @{handle}")
                except Exception as e:
                    print(f"  Error following @{handle}: {e}")

            print(f"\n✅ Total new AI leaders followed: {followed_count}")

        finally:
            ctx.close()

if __name__ == "__main__":
    unfollow_and_rebalance()
