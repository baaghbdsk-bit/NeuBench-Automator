"""
Exports all active authenticated browser sessions (X, LinkedIn, Threads, Reddit)
into portable, cross-platform storage states (cookies & origins) for cloud deployment.
"""
import sys
import os
import json
import base64
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from playwright.sync_api import sync_playwright
import config

EXPORT_DIR = BASE_DIR / "cloud_exports"
EXPORT_DIR.mkdir(exist_ok=True)

sessions = [
    {
        "name": "X",
        "env_var": "X_COOKIES_BASE64",
        "user_data_dir": config.USER_DATA_DIR,
        "export_file": EXPORT_DIR / "x_storage.json",
        "target_url": "https://x.com/home"
    },
    {
        "name": "LinkedIn",
        "env_var": "LINKEDIN_COOKIES_BASE64",
        "user_data_dir": config.LINKEDIN_USER_DATA_DIR,
        "export_file": EXPORT_DIR / "linkedin_storage.json",
        "target_url": "https://www.linkedin.com/feed/"
    },
    {
        "name": "Threads",
        "env_var": "THREADS_COOKIES_BASE64",
        "user_data_dir": config.BASE_DIR / "threads_session",
        "export_file": EXPORT_DIR / "threads_storage.json",
        "target_url": "https://www.threads.net/"
    },
    {
        "name": "Reddit",
        "env_var": "REDDIT_COOKIES_BASE64",
        "user_data_dir": config.BASE_DIR / "reddit_session",
        "export_file": EXPORT_DIR / "reddit_storage.json",
        "target_url": "https://www.reddit.com/"
    }
]

exported_env = {}

with sync_playwright() as p:
    for s in sessions:
        name = s["name"]
        d = s["user_data_dir"]
        export_p = s["export_file"]
        env_var = s["env_var"]

        print(f"📦 Exporting session for {name} from {d.name}...")
        if not d.exists() or not any(d.iterdir()):
            print(f"  ⚠️ Skipping {name}: directory does not exist or empty.")
            continue

        try:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(d),
                headless=True,
                viewport={"width": 1280, "height": 800},
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            # Dump storage state
            state = ctx.storage_state()
            ctx.close()

            # Save json
            export_p.write_text(json.dumps(state, indent=2), encoding="utf-8")
            raw_b64 = base64.b64encode(json.dumps(state).encode("utf-8")).decode("utf-8")
            exported_env[env_var] = raw_b64
            print(f"  ✅ {name} exported! Cookies: {len(state.get('cookies', []))}, Size: {len(raw_b64)} chars")
        except Exception as e:
            print(f"  ❌ Error exporting {name}: {e}")

print("\n🎉 All active sessions exported successfully to", EXPORT_DIR)
# Also save exported base64 map for automatic GitHub secret syncing
secrets_file = EXPORT_DIR / "github_secrets.json"
secrets_file.write_text(json.dumps(exported_env, indent=2), encoding="utf-8")
print(f"Secrets mapping saved to {secrets_file}")
