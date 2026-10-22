import os
import sys
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

handle = os.getenv("BLUESKY_HANDLE", "neubench.bsky.social")
app_pwd = os.getenv("BLUESKY_APP_PASSWORD", "")

print(f"[Bluesky Follower] Connecting as {handle}...")
session_res = requests.post(
    "https://bsky.social/xrpc/com.atproto.server.createSession",
    json={"identifier": handle, "password": app_pwd},
    timeout=10
)

if session_res.status_code != 200:
    print(f"Auth failed: {session_res.text}")
    sys.exit(1)

session = session_res.json()
jwt = session["accessJwt"]
my_did = session["did"]
headers = {"Authorization": f"Bearer {jwt}"}

# Top influential AI researchers, open source devs, and tech leaders on Bluesky
TARGET_ACCOUNTS = [
    "simonw.net",             # Simon Willison (LLMs & Open Source pioneer)
    "swyx.io",                # Latent Space / AI Engineer Foundation
    "jay.bsky.team",          # Jay Graber (CEO of Bluesky)
    "why.bsky.team",          # Bluesky core team
    "emostaque.bsky.social",  # Emad Mostaque (Stability AI founder, open weights)
    "bindureddy.bsky.social", # Abacus.ai CEO
    "ylecun.bsky.social",     # Yann LeCun (Chief AI Scientist Meta)
    "karpathy.bsky.social",   # Andrej Karpathy
    "danieldk.org",           # Open Source AI Rust engineer
    "drjimfan.bsky.social",   # Jim Fan (NVIDIA AI)
]

def resolve_handle(target_handle: str) -> str:
    try:
        r = requests.get(
            f"https://bsky.social/xrpc/com.atproto.identity.resolveHandle?handle={target_handle}",
            timeout=5
        )
        if r.status_code == 200:
            return r.json().get("did")
    except Exception as e:
        print(f"Error resolving {target_handle}: {e}")
    return None

def follow_user(target_did: str, target_handle: str):
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    record = {
        "$type": "app.bsky.graph.follow",
        "subject": target_did,
        "createdAt": now_iso
    }
    r = requests.post(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord",
        headers=headers,
        json={
            "repo": my_did,
            "collection": "app.bsky.graph.follow",
            "record": record
        },
        timeout=10
    )
    if r.status_code == 200:
        print(f"✅ Followed @{target_handle}")
        return True
    else:
        print(f"Failed to follow @{target_handle}: {r.status_code} {r.text}")
        return False

print("\n--- Following Top AI & Tech Leaders on Bluesky ---")
followed_count = 0
for h in TARGET_ACCOUNTS:
    did = resolve_handle(h)
    if did:
        if follow_user(did, h):
            followed_count += 1
    else:
        print(f"⚠️ Could not resolve @{h}")

print(f"\nCompleted! Successfully followed {followed_count} accounts on Bluesky.")

