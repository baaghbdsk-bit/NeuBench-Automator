"""
Bluesky Client for NeuBench-Automator.
Uses official AT Protocol XRPC REST endpoints (100% free, no paid API keys, official protocol).
"""
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
import requests


class BlueskyClient:
    def __init__(self, handle: str = "", app_password: str = "", dry_run: bool = False):
        self.handle = handle.strip() if handle else ""
        self.app_password = app_password.strip() if app_password else ""
        self.dry_run = dry_run
        self.session: Optional[Dict[str, Any]] = None

    def is_configured(self) -> bool:
        return bool(self.handle and self.app_password)

    def login(self) -> Tuple[bool, str]:
        if not self.is_configured():
            return False, "Bluesky handle and app password not configured in .env."

        url = "https://bsky.social/xrpc/com.atproto.server.createSession"
        try:
            res = requests.post(
                url,
                json={"identifier": self.handle, "password": self.app_password},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if res.status_code == 200:
                self.session = res.json()
                return True, "Login successful"
            else:
                return False, f"Bluesky authentication failed: {res.text}"
        except Exception as e:
            return False, f"Bluesky network error: {e}"

    def post(self, text: str) -> Tuple[bool, str]:
        """Publishes a text post to Bluesky AT Protocol."""
        if self.dry_run:
            return True, f"[DRY RUN] Bluesky post simulated: {text[:60]}..."

        if not self.is_configured():
            return False, "Bluesky credentials not configured. Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD in .env."

        if not self.session:
            ok, msg = self.login()
            if not ok:
                return False, msg

        url = "https://bsky.social/xrpc/com.atproto.repo.createRecord"
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        payload = {
            "repo": self.session["did"],
            "collection": "app.bsky.feed.post",
            "record": {
                "$type": "app.bsky.feed.post",
                "text": text,
                "createdAt": now_iso
            }
        }

        headers = {
            "Authorization": f"Bearer {self.session['accessJwt']}",
            "Content-Type": "application/json"
        }

        try:
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                return True, "Post published to Bluesky successfully!"
            else:
                return False, f"Bluesky posting error: {res.text}"
        except Exception as e:
            return False, f"Bluesky network error: {e}"
