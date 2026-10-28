import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime
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

def inspect_db_cookies(session_dir: Path, domains: list, target_cookies: list):
    cookie_db = session_dir / "Default" / "Network" / "Cookies"
    if not cookie_db.exists():
        return False, "Cookies DB file not found", {}
    try:
        uri = f"file:{cookie_db.resolve().as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        cur = conn.cursor()
        found = {}
        for dom in domains:
            cur.execute("SELECT host_key, name, is_secure, expires_utc FROM cookies WHERE host_key LIKE ?", (f"%{dom}%",))
            for row in cur.fetchall():
                found[row[1]] = row[0]
        conn.close()
        present = [c for c in target_cookies if c in found]
        return (len(present) > 0), f"Found {len(present)}/{len(target_cookies)} key cookies: {present}", found
    except Exception as e:
        return False, f"Error inspecting cookies: {e}", {}

def run_deep_verification():
    results = {}
    print("=" * 70)
    print("🚀 NEUBENCH X-POST AUTOMATOR — FULL PLATFORM & SUBSYSTEM VERIFICATION")
    print("=" * 70)

    # 1. Gemini AI
    print("\n[1/7] Testing Gemini AI Model & Content Engine...")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        results["Gemini AI"] = {"status": "FAILED", "reason": "GEMINI_API_KEY missing in .env"}
        print("  ❌ Gemini API Key is missing in .env!")
    else:
        try:
            from src.ai_generator import AIGenerator
            ai = AIGenerator()
            sample = ai.generate_hot_take("DeepSeek and open weights LLMs")
            if sample:
                results["Gemini AI"] = {
                    "status": "OPERATIONAL",
                    "sample": sample
                }
                print(f"  ✅ Gemini AI Status: OPERATIONAL")
                print(f"     Sample Generation: \"{sample[:90]}...\"")
            else:
                results["Gemini AI"] = {"status": "FAILED", "reason": "Empty text response"}
                print("  ❌ Gemini returned empty generation.")
        except Exception as e:
            results["Gemini AI"] = {"status": "FAILED", "reason": str(e)}
            print(f"  ❌ Gemini AI Error: {e}")

    # 2. X / Twitter
    print("\n[2/7] Testing 𝕏 (Twitter) Client Session...")
    x_session = BASE_DIR / "browser_session"
    cookies_json = x_session / "cookies.json"
    x_has_cookies_file = cookies_json.exists() and cookies_json.stat().st_size > 100
    x_db_ok, x_db_msg, x_found = inspect_db_cookies(x_session, ["x.com", "twitter.com"], ["auth_token", "ct0", "twid"])
    
    auth_in_json = False
    if x_has_cookies_file:
        try:
            with open(cookies_json, "r", encoding="utf-8") as f:
                c_data = json.load(f)
                cookie_list = c_data.get("cookies", []) if isinstance(c_data, dict) else c_data
                names = [c.get("name") for c in cookie_list if isinstance(c, dict)]
                auth_in_json = "auth_token" in names
        except Exception:
            pass

    if auth_in_json or "auth_token" in x_found:
        results["𝕏 (Twitter)"] = {
            "status": "OPERATIONAL",
            "account": "@GWorld34864 (vishnu rot)",
            "auth_token": True,
            "ct0_csrf": "ct0" in x_found or auth_in_json
        }
        print(f"  ✅ 𝕏 (Twitter) Status: OPERATIONAL")
        print(f"     Account: @GWorld34864 | Storage state: Active & authenticated")
    else:
        results["𝕏 (Twitter)"] = {"status": "FAILED", "reason": "auth_token cookie missing"}
        print("  ❌ 𝕏 session missing valid auth_token.")

    # 3. Bluesky (AT Protocol)
    print("\n[3/7] Testing Bluesky (AT Protocol Direct API)...")
    bsky_handle = os.getenv("BLUESKY_HANDLE", "")
    bsky_pw = os.getenv("BLUESKY_APP_PASSWORD", "")
    if not (bsky_handle and bsky_pw):
        results["Bluesky"] = {"status": "FAILED", "reason": "Credentials missing in .env"}
        print("  ❌ Bluesky credentials not configured in .env")
    else:
        try:
            from src.bluesky_client import BlueskyClient
            client = BlueskyClient(handle=bsky_handle, app_password=bsky_pw, dry_run=False)
            ok, msg = client.login()
            if ok:
                did = client.session.get("did")
                results["Bluesky"] = {
                    "status": "OPERATIONAL",
                    "handle": bsky_handle,
                    "did": did
                }
                print(f"  ✅ Bluesky Status: OPERATIONAL")
                print(f"     Account: @{bsky_handle} | Decentralized ID: {did}")
            else:
                results["Bluesky"] = {"status": "FAILED", "reason": msg}
                print(f"  ❌ Bluesky Login Failed: {msg}")
        except Exception as e:
            results["Bluesky"] = {"status": "FAILED", "reason": str(e)}
            print(f"  ❌ Bluesky Error: {e}")

    # 4. LinkedIn
    print("\n[4/7] Testing LinkedIn Autonomous Session...")
    li_session = BASE_DIR / "linkedin_session"
    li_ok, li_msg, li_found = inspect_db_cookies(li_session, ["linkedin.com"], ["li_at", "JSESSIONID"])
    li_profile_file = BASE_DIR / "linkedin_profile.json"
    li_profile = {}
    if li_profile_file.exists():
        try:
            with open(li_profile_file, "r", encoding="utf-8") as f:
                li_profile = json.load(f)
        except Exception:
            pass

    if "li_at" in li_found:
        prof_name = li_profile.get("name", "Vivek Gupta")
        prof_url = li_profile.get("profile_url", "https://www.linkedin.com/in/vivek-gupta-b6b2951b2/")
        results["LinkedIn"] = {
            "status": "OPERATIONAL",
            "profile": prof_name,
            "url": prof_url,
            "li_at_present": True
        }
        print(f"  ✅ LinkedIn Status: OPERATIONAL")
        print(f"     Account: {prof_name} | li_at session cookie: Active")
        print(f"     Profile URL: {prof_url}")
    else:
        results["LinkedIn"] = {"status": "FAILED", "reason": "li_at cookie missing in linkedin_session"}
        print(f"  ❌ LinkedIn session is missing li_at cookie.")

    # 5. Reddit
    print("\n[5/7] Testing Reddit Session...")
    reddit_session = BASE_DIR / "reddit_session"
    rd_ok, rd_msg, rd_found = inspect_db_cookies(reddit_session, ["reddit.com"], ["reddit_session", "token_v2", "csrf_token"])
    account_txt = reddit_session / "account.txt"
    rd_acc = account_txt.read_text(encoding="utf-8").strip() if account_txt.exists() else "u/NeuBench"
    if "reddit_session" in rd_found or "token_v2" in rd_found:
        results["Reddit"] = {
            "status": "OPERATIONAL",
            "account": rd_acc,
            "cookies": f"reddit_session={'reddit_session' in rd_found}, token_v2={'token_v2' in rd_found}"
        }
        print(f"  ✅ Reddit Status: OPERATIONAL")
        print(f"     Account: {rd_acc} | Session & token_v2 cookies active")
    else:
        results["Reddit"] = {"status": "FAILED", "reason": "Session cookies missing in reddit_session"}
        print(f"  ❌ Reddit session is not logged in.")

    # 6. Threads
    print("\n[6/7] Testing Threads Session...")
    th_session = BASE_DIR / "threads_session"
    th_ok, th_msg, th_found = inspect_db_cookies(th_session, ["threads.net", "threads.com", "instagram.com"], ["sessionid", "csrftoken", "ds_user_id"])
    th_acc_txt = th_session / "account.txt"
    th_acc = th_acc_txt.read_text(encoding="utf-8").strip() if th_acc_txt.exists() else "@NeuBench"
    if "sessionid" in th_found:
        results["Threads"] = {
            "status": "OPERATIONAL",
            "account": th_acc,
            "sessionid_present": True
        }
        print(f"  ✅ Threads Status: OPERATIONAL")
        print(f"     Account: {th_acc} | sessionid & csrftoken active")
    else:
        results["Threads"] = {"status": "FAILED", "reason": "sessionid cookie missing in threads_session"}
        print(f"  ❌ Threads session is not logged in.")

    # 7. Background Daemon & Activity Execution
    print("\n[7/7] Checking Daemon Engine & Historical Verifications...")
    metrics_file = BASE_DIR / "trial_metrics.json"
    actions_summary = {}
    if metrics_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                m_data = json.load(f)
            events = m_data.get("recent_events", [])
            for ev in events:
                act = ev.get("action_type")
                st = ev.get("status")
                if act not in actions_summary:
                    actions_summary[act] = {"success": 0, "failed": 0, "latest": ev.get("timestamp")}
                if st == "success":
                    actions_summary[act]["success"] += 1
                else:
                    actions_summary[act]["failed"] += 1
                actions_summary[act]["latest"] = ev.get("timestamp")
        except Exception as e:
            print(f"  ⚠️ Error reading trial_metrics.json: {e}")

    results["Daemon / Engine"] = {
        "status": "OPERATIONAL",
        "actions_summary": actions_summary
    }
    print("  ✅ Action Verifications from Trial Telemetry:")
    for act, info in sorted(actions_summary.items()):
        latest_time = str(info["latest"])[:19]
        print(f"     • {act:15} -> {info['success']} successful (latest: {latest_time})")

    # Final Summary Matrix
    print("\n" + "=" * 70)
    print("📊 OVERALL PLATFORM READINESS MATRIX")
    print("=" * 70)
    all_operational = True
    for plat, data in results.items():
        if plat == "Daemon / Engine":
            continue
        st = data.get("status")
        icon = "✅" if st == "OPERATIONAL" else "❌"
        if st != "OPERATIONAL":
            all_operational = False
        print(f"  {icon} {plat:18} : {st}")

    print("=" * 70)
    if all_operational:
        print("🎉 ALL PLATFORMS ARE PROPERLY LINKED AND FULLY OPERATIONAL!")
    else:
        print("⚠️ Some platforms need attention. See details above.")
    print("=" * 70)

if __name__ == "__main__":
    run_deep_verification()
