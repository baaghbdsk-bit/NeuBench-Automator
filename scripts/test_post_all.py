import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / ".env")

import config
from src.ai_generator import AIGenerator
from src.tracker import ActivityTracker

tracker = ActivityTracker(BASE_DIR / "trial_metrics.json", BASE_DIR / "post_history.json")
ai = AIGenerator()

def post_all_test():
    print("=" * 70)
    print("🚀 LIVE TEST RUN: PUBLISHING 1 TEST POST ACROSS ALL 5 PLATFORMS")
    print("=" * 70)

    results = {}
    title = "Real-Time LLM Latency & Inference Velocity"
    summary = "NeuBench evaluates real-world speed vs cost trade-offs across 260+ frontier and open-weight models."
    company = "NeuBench"

    # 1. Bluesky
    print("\n[1/5] Posting to Bluesky (AT Protocol)...")
    try:
        from src.bluesky_client import BlueskyClient
        bsky = BlueskyClient(handle=config.BLUESKY_HANDLE, app_password=config.BLUESKY_APP_PASSWORD, dry_run=False)
        bsky_text = ai.generate_bluesky_take(title=title, summary=summary, company=company)
        print(f"Draft: {bsky_text}")
        t0 = time.time()
        ok, msg = bsky.post(bsky_text)
        dur = time.time() - t0
        if ok:
            results["Bluesky"] = {"status": "SUCCESS", "message": msg}
            print(f"  ✅ Bluesky: Published successfully! ({msg})")
            tracker.record_event("bluesky_post", "success", "Bluesky (@neubench.bsky.social)", bsky_text[:80], dur, False)
        else:
            results["Bluesky"] = {"status": "FAILED", "message": msg}
            print(f"  ❌ Bluesky Failed: {msg}")
    except Exception as e:
        results["Bluesky"] = {"status": "ERROR", "message": str(e)}
        print(f"  ❌ Bluesky Exception: {e}")

    # 2. Twitter / 𝕏
    print("\n[2/5] Posting to 𝕏 (Twitter)...")
    try:
        from src.twitter_client import TwitterClient
        tw = TwitterClient(headless=True, dry_run=False)
        tw_text = ai.generate_neubench_take(title=title, summary=summary, company=company)
        print(f"Draft: {tw_text}")
        t0 = time.time()
        ok = tw.post_tweet(tw_text)
        dur = time.time() - t0
        if ok:
            results["Twitter / 𝕏"] = {"status": "SUCCESS", "message": "Tweet posted successfully!"}
            print(f"  ✅ 𝕏 (Twitter): Published successfully!")
            tracker.record_event("original_post", "success", "𝕏 Feed", tw_text[:80], dur, False)
        else:
            results["Twitter / 𝕏"] = {"status": "FAILED", "message": "Failed to post tweet via browser."}
            print(f"  ❌ 𝕏 (Twitter) Failed!")
    except Exception as e:
        results["Twitter / 𝕏"] = {"status": "ERROR", "message": str(e)}
        print(f"  ❌ 𝕏 (Twitter) Exception: {e}")

    # 3. LinkedIn
    print("\n[3/5] Posting to LinkedIn...")
    try:
        from src.linkedin_automater import LinkedInAutomater
        li = LinkedInAutomater(headless=True, dry_run=False)
        li_text = ai.generate_linkedin_take(title=title, summary=summary, company=company)
        print(f"Draft: {li_text[:120]}...")
        t0 = time.time()
        ok, msg = li.post(li_text)
        dur = time.time() - t0
        if ok:
            results["LinkedIn"] = {"status": "SUCCESS", "message": msg}
            print(f"  ✅ LinkedIn: {msg}")
            tracker.record_event("linkedin_post", "success", "LinkedIn B2B", li_text[:80], dur, False)
        else:
            results["LinkedIn"] = {"status": "FAILED", "message": msg}
            print(f"  ⚠️ LinkedIn Result: {msg}")
    except Exception as e:
        results["LinkedIn"] = {"status": "ERROR", "message": str(e)}
        print(f"  ❌ LinkedIn Exception: {e}")

    # 4. Threads
    print("\n[4/5] Posting to Threads...")
    try:
        from src.threads_automater import ThreadsAutomater
        th = ThreadsAutomater(headless=True, dry_run=False)
        th_text = ai.generate_threads_take(title=title, summary=summary, company=company)
        print(f"Draft: {th_text[:100]}...")
        t0 = time.time()
        ok, msg = th.post(th_text)
        dur = time.time() - t0
        if ok:
            results["Threads"] = {"status": "SUCCESS", "message": msg}
            print(f"  ✅ Threads: {msg}")
            tracker.record_event("threads_post", "success", "Threads Community", th_text[:80], dur, False)
        else:
            results["Threads"] = {"status": "FAILED", "message": msg}
            print(f"  ⚠️ Threads Result: {msg}")
    except Exception as e:
        results["Threads"] = {"status": "ERROR", "message": str(e)}
        print(f"  ❌ Threads Exception: {e}")

    # 5. Reddit
    print("\n[5/5] Posting to Reddit (r/test)...")
    try:
        from src.reddit_automater import RedditAutomater
        rd = RedditAutomater(headless=False, dry_run=False)
        rd_data = ai.generate_reddit_post(
            title="Evaluating Real-World Token Latency & Throughput across LLM APIs",
            summary="NeuBench evaluations show real-world token throughput variances up to 40% across hosted endpoints.",
            company="NeuBench",
            subreddit="r/test"
        )
        r_title = rd_data.get("title", "LLM Latency & Throughput Benchmark Analysis")
        r_body = rd_data.get("body", "NeuBench evaluation tests.")
        print(f"Title: {r_title}")
        print(f"Body preview: {r_body[:100]}...")
        t0 = time.time()
        ok, msg = rd.post("test", r_title, r_body)
        dur = time.time() - t0
        if ok:
            results["Reddit"] = {"status": "SUCCESS", "message": msg}
            print(f"  ✅ Reddit: {msg}")
            tracker.record_event("reddit_post", "success", "r/test", r_title[:80], dur, False)
        else:
            results["Reddit"] = {"status": "FAILED", "message": msg}
            print(f"  ⚠️ Reddit Result: {msg}")
    except Exception as e:
        results["Reddit"] = {"status": "ERROR", "message": str(e)}
        print(f"  ❌ Reddit Exception: {e}")

    print("\n" + "=" * 70)
    print("📊 MULTI-PLATFORM TEST SUMMARY")
    print("=" * 70)
    for p, info in results.items():
        st = info.get("status")
        icon = "✅" if st == "SUCCESS" else "⚠️" if st == "FAILED" else "❌"
        print(f"  {icon} {p:15}: {st} ({info.get('message', '')})")
    print("=" * 70)

if __name__ == "__main__":
    post_all_test()
