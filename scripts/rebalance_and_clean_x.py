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

# Non-tech / unrelated accounts to unfollow
UNRELATED_ACCOUNTS = [
    "rishibagree",
    "JaipurDialogues",
    "ARanganathan72",
    "Genbakshi_in",
    "ajeetbharti",
    "iamharshbeniwal",
    "KlRajiv",
    "TheNavroopSingh",
    "ajaykraina",
    "atsshow7",
    "We_IndianIN",
    "SirPareshRawal",
    "majorgauravarya",
    "AadiAchint",
    "Sanjay_Dixit",
    "shambhav15",
    "Iyervval",
    "SushantBSinha",
    "realsiff",
    "SudhanshuTrived",
    "AshwiniUpadhyay",
    "AbhijitChavda",
    "ankitatIIMA",
    "XuanzhenZ",
    "ETH_Daily",
    "CoinMarketCap",
    "BitlayerLabs",
    "CygnusFi",
    "LorenzoProtocol",
    "BinanceWallet",
    "plumenetwork"
]

# Top tier AI leaders to follow
AI_LEADERS_TO_FOLLOW = [
    "AndrewYNg",
    "JeffDean",
    "AnthropicAI",
    "drjimfan",
    "svpino",
    "huggingface"
]

def run_rebalance():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(config.USER_DATA_DIR),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            print("==================================================")
            print("🚀 STEP 1: Unfollowing Unrelated Accounts")
            print("==================================================")
            unfollowed_count = 0
            for handle in UNRELATED_ACCOUNTS:
                try:
                    print(f"Checking @{handle}...")
                    page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(2000)

                    # Look for unfollow button
                    unfollow_btn = page.locator('button[data-testid$="-unfollow"]').first
                    if unfollow_btn.is_visible():
                        unfollow_btn.click()
                        page.wait_for_timeout(1000)
                        confirm = page.locator('[data-testid="confirmationSheetConfirm"]').first
                        if confirm.is_visible():
                            confirm.click()
                            unfollowed_count += 1
                            print(f"  ❌ Unfollowed @{handle} (#{unfollowed_count})")
                            time.sleep(random.uniform(1.5, 2.5))
                        else:
                            print(f"  Confirmation modal not found for @{handle}")
                    else:
                        print(f"  Not following @{handle}")
                except Exception as e:
                    print(f"  Error with @{handle}: {e}")

            print(f"\n✅ Total unrelated accounts unfollowed: {unfollowed_count}")

            print("\n==================================================")
            print("🚀 STEP 2: Following Top AI Leaders")
            print("==================================================")
            followed_count = 0
            for handle in AI_LEADERS_TO_FOLLOW:
                try:
                    print(f"Visiting @{handle}...")
                    page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(2000)

                    # Check if already following
                    unfollow_btn = page.locator('button[data-testid$="-unfollow"]').first
                    if unfollow_btn.is_visible():
                        print(f"  Already following @{handle}")
                        continue

                    # Click follow
                    follow_btn = page.locator('button[data-testid$="-follow"]').first
                    if follow_btn.is_visible():
                        follow_btn.click()
                        followed_count += 1
                        print(f"  ➕ Followed @{handle} (#{followed_count})")
                        time.sleep(random.uniform(1.8, 3.0))
                    else:
                        print(f"  Follow button not found on @{handle}")
                except Exception as e:
                    print(f"  Error with @{handle}: {e}")

            print(f"\n✅ Total new AI leaders followed: {followed_count}")

        finally:
            ctx.close()

if __name__ == "__main__":
    run_rebalance()
