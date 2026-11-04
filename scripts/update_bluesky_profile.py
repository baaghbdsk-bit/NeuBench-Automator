import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

handle = os.getenv("BLUESKY_HANDLE", "neubench.bsky.social")
app_pwd = os.getenv("BLUESKY_APP_PASSWORD", "")

print(f"[Bluesky] Connecting as {handle}...")
session_res = requests.post(
    "https://bsky.social/xrpc/com.atproto.server.createSession",
    json={"identifier": handle, "password": app_pwd},
    timeout=10
)

if session_res.status_code != 200:
    print(f"[Bluesky] Failed to authenticate: {session_res.text}")
    sys.exit(1)

session = session_res.json()
jwt = session["accessJwt"]
did = session["did"]
headers = {"Authorization": f"Bearer {jwt}"}

def upload_blob(file_path: Path):
    if not file_path.exists():
        print(f"File {file_path} not found")
        return None
    print(f"Uploading {file_path.name}...")
    with open(file_path, "rb") as f:
        data = f.read()
    
    upload_headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "image/jpeg"
    }
    r = requests.post(
        "https://bsky.social/xrpc/com.atproto.repo.uploadBlob",
        headers=upload_headers,
        data=data,
        timeout=20
    )
    if r.status_code == 200:
        print(f"Uploaded {file_path.name} successfully!")
        return r.json()["blob"]
    else:
        print(f"Upload failed for {file_path.name}: {r.status_code} {r.text}")
        return None

avatar_blob = upload_blob(Path("assets/neubench_avatar.jpg"))
banner_blob = upload_blob(Path("assets/neubench_twitter_banner.jpg"))

profile_record = {
    "$type": "app.bsky.actor.profile",
    "displayName": "NeuBench",
    "description": (
        "NeuBench: Real-time AI evals across 260+ models.\n\n"
        "🌐 App: https://app.neubench.workers.dev\n"
        "𝕏: x.com/GWorld34864\n"
        "🧵 Threads: threads.net/@neubench\n"
        "💼 LinkedIn: in/vishnu-gupta-b6b2951b2\n"
        "👽 Reddit: u/Express-Cucumber-478"
    )
}

if avatar_blob:
    profile_record["avatar"] = avatar_blob
if banner_blob:
    profile_record["banner"] = banner_blob

put_res = requests.post(
    "https://bsky.social/xrpc/com.atproto.repo.putRecord",
    headers=headers,
    json={
        "repo": did,
        "collection": "app.bsky.actor.profile",
        "rkey": "self",
        "record": profile_record
    },
    timeout=10
)

if put_res.status_code == 200:
    print("✅ Bluesky profile updated successfully with all 4 platforms & app URL!")
    print(f"URL: https://bsky.app/profile/{handle}")
else:
    print(f"❌ Failed to update Bluesky profile: {put_res.status_code} {put_res.text}")
