import os
import sys
import requests
from pathlib import Path
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

print(f"[Bluesky] Authenticated! DID: {did}")

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

avatar_blob = upload_blob(Path("avatar.jpg"))
banner_blob = upload_blob(Path("assets/neubench_twitter_banner.jpg"))

existing_profile = {}
get_record = requests.get(
    f"https://bsky.social/xrpc/com.atproto.repo.getRecord?repo={did}&collection=app.bsky.actor.profile&rkey=self",
    headers=headers,
    timeout=10
)
if get_record.status_code == 200:
    existing_profile = get_record.json().get("value", {})

profile_record = {
    "$type": "app.bsky.actor.profile",
    "displayName": "NeuBench",
    "description": "Frontier AI Benchmarks, real-time model evals & autonomous open-source intelligence across 266+ LLMs.\n\nLive leaderboard: neubench.vercel.app"
}

if avatar_blob:
    profile_record["avatar"] = avatar_blob
elif "avatar" in existing_profile:
    profile_record["avatar"] = existing_profile["avatar"]

if banner_blob:
    profile_record["banner"] = banner_blob
elif "banner" in existing_profile:
    profile_record["banner"] = existing_profile["banner"]

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
    print("[Bluesky] Profile updated successfully on AT Protocol!")
    print(f"View live profile at: https://bsky.app/profile/{handle}")
else:
    print(f"[Bluesky] Failed to update profile record: {put_res.status_code} {put_res.text}")
