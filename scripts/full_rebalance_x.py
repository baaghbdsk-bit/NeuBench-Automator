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

# Remaining unrelated accounts to unfollow
TO_UNFOLLOW = [
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
    "Data_Ecosystem",
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
TO_FOLLOW = [
    "AndrewYNg",
    "JeffDean",
    "AnthropicAI",
    "drjimfan",
    "svpino",
    "huggingface"
]

def full_rebalance():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(config.USER_DATA_DIR),
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            print("==================================================")
            print(f"🚀 STEP 1: Unfollowing {len(TO_UNFOLLOW)} Unrelated Accounts")
            print("==================================================")
            unfollowed_count = 0
            for idx, handle in enumerate(TO_UNFOLLOW):
                try:
                    print(f"[{idx+1}/{len(TO_UNFOLLOW)}] Checking @{handle}...")
                    page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(2000)

                    unfollow_btn = page.locator('button[data-testid$="-unfollow"]').first
                    if unfollow_btn.is_visible():
                        unfollow_btn.click()
                        page.wait_for_timeout(1000)

                        confirm = page.locator('[data-testid="confirmationSheetConfirm"]').first
                        if confirm.is_visible():
                            confirm.click()
                            unfollowed_count += 1
                            print(f"  ❌ Unfollowed @{handle} (#{unfollowed_count})")
                            time.sleep(random.uniform(1.2, 2.2))
                        else:
                            print(f"  Confirm dialog not visible for @{handle}")
                    else:
                        print(f"  Not following @{handle}")
                except Exception as e:
                    print(f"  Error on @{handle}: {e}")

            print(f"\n✅ Finished! Total accounts unfollowed in this step: {unfollowed_count}")

            print("\n==================================================")
            print(f"🚀 STEP 2: Following {len(TO_FOLLOW)} Top AI Leaders")
            print("==================================================")
            followed_count = 0
            for idx, handle in enumerate(TO_FOLLOW):
                try:
                    print(f"[{idx+1}/{len(TO_FOLLOW)}] Visiting @{handle}...")
                    page.goto(f"https://x.com/{handle}", wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(2000)

                    # Check if already following
                    unfollow_btn = page.locator('button[data-testid$="-unfollow"]').first
                    if unfollow_btn.is_visible():
                        print(f"  Already following @{handle}")
                        continue

                    follow_btn = page.locator('button[data-testid$="-follow"]').first
                    if follow_btn.is_visible():
                        follow_btn.click()
                        followed_count += 1
                        print(f"  ➕ Followed @{handle} (#{followed_count})")
                        time.sleep(random.uniform(1.8, 3.0))
                    else:
                        print(f"  Follow button not found on @{handle}")
                except Exception as e:
                    print(f"  Error on @{handle}: {e}")

            print(f"\n✅ Finished! Total new AI leaders followed: {followed_count}")

        finally:
            ctx.close()

if __name__ == "__main__":
    full_rebalance()
