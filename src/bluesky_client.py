"""
Bluesky Client for NeuBench-Automator.
Uses official AT Protocol XRPC REST endpoints (100% free, no paid API keys, official protocol).
"""
import re
import time
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
import requests


def detect_facets(text: str) -> List[Dict[str, Any]]:
    """
    Parses URLs from text and creates AT Protocol facets (app.bsky.richtext.facet)
    using UTF-8 byte indices so URLs render as clickable hyperlinks on Bluesky.
    """
    facets = []
    
    # URL pattern (http, https or bare domains like app.neubench.workers.dev)
    url_regex = re.compile(r"(https?://[^\s()<>]+|neubench\.vercel\.app[^\s()<>]*)")
    for match in url_regex.finditer(text):
        raw_url = match.group(0).rstrip(".,!?:;)'\"")
        full_url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"
        
        start_char = match.start()
        end_char = start_char + len(raw_url)
        
        byte_start = len(text[:start_char].encode("utf-8"))
        byte_end = len(text[:end_char].encode("utf-8"))
        
        facets.append({
            "index": {
                "byteStart": byte_start,
                "byteEnd": byte_end
            },
            "features": [{
                "$type": "app.bsky.richtext.facet#link",
                "uri": full_url
            }]
        })
    return facets


class BlueskyClient:
    def __init__(self, handle: str = "", app_password: str = "", dry_run: bool = False):
        self.handle = handle.strip() if handle else ""
        self.app_password = app_password.strip() if app_password else ""
        self.dry_run = dry_run
        self.session: Optional[Dict[str, Any]] = None
        self.last_outcome_unknown = False
        self.last_message = ""

    def _reset_outcome(self):
        self.last_outcome_unknown = False
        self.last_message = ""

    def _finish(self, success: bool, message: str, unknown: bool = False) -> Tuple[bool, str]:
        self.last_outcome_unknown = unknown
        self.last_message = message
        return success, message

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

    def upload_blob(self, file_path: str, mime_type: str = "image/png") -> Optional[Dict[str, Any]]:
        """Uploads a media blob (image/GIF/video) to Bluesky XRPC endpoint."""
        if not self.session:
            ok, _ = self.login()
            if not ok:
                return None
        url = "https://bsky.social/xrpc/com.atproto.repo.uploadBlob"
        headers = {
            "Authorization": f"Bearer {self.session['accessJwt']}",
            "Content-Type": mime_type
        }
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            res = requests.post(url, data=data, headers=headers, timeout=25)
            if res.status_code == 200:
                return res.json().get("blob")
            else:
                print(f"[BlueskyClient] Blob upload failed ({res.status_code}): {res.text}")
                return None
        except Exception as e:
            print(f"[BlueskyClient] Blob upload error: {e}")
            return None

    def post(self, text: str, media_path: Optional[str] = None) -> Tuple[bool, str]:
        """Publishes a post to Bluesky AT Protocol with optional media embed and automatic URL facets."""
        self._reset_outcome()
        if self.dry_run:
            return self._finish(True, f"[DRY RUN] Bluesky post simulated: {text[:60]}...")

        text = str(text or "").strip()
        if not text:
            return self._finish(False, "Bluesky post text is empty.")
        if len(text) > 295:
            text = text[:292].rsplit(" ", 1)[0].rstrip(".,:;") + "..."

        if not self.is_configured():
            return self._finish(False, "Bluesky credentials not configured. Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD in .env.")

        if not self.session:
            ok, msg = self.login()
            if not ok:
                return self._finish(False, msg)

        url = "https://bsky.social/xrpc/com.atproto.repo.createRecord"
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        record: Dict[str, Any] = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": now_iso
        }

        # Add clickable facets for any URLs
        facets = detect_facets(text)
        if facets:
            record["facets"] = facets

        # Attach image/GIF if provided
        if media_path and os.path.exists(media_path):
            mime = "image/gif" if media_path.endswith(".gif") else "image/png"
            blob = self.upload_blob(media_path, mime_type=mime)
            if blob:
                record["embed"] = {
                    "$type": "app.bsky.embed.images",
                    "images": [
                        {
                            "alt": "NeuBench Technical Architecture and Benchmark Visualizer",
                            "image": blob
                        }
                    ]
                }

        payload = {
            "repo": self.session["did"],
            "collection": "app.bsky.feed.post",
            "record": record
        }

        headers = {
            "Authorization": f"Bearer {self.session['accessJwt']}",
            "Content-Type": "application/json"
        }

        try:
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                uri = data.get("uri", "")
                return self._finish(True, f"Post published to Bluesky successfully! (URI: {uri})")
            else:
                return self._finish(False, f"Bluesky posting error: {res.text}")
        except Exception as e:
            return self._finish(False, f"Bluesky network error after submission: {e}", unknown=True)


    def search_viral_posts(self, query: str = "AI LLM benchmark", limit: int = 5) -> List[Dict[str, Any]]:
        """Searches top relevant posts on Bluesky via XRPC API."""
        if not self.session:
            ok, _ = self.login()
            if not ok:
                return []
        url = "https://bsky.social/xrpc/app.bsky.feed.searchPosts"
        headers = {"Authorization": f"Bearer {self.session['accessJwt']}"}
        try:
            res = requests.get(url, params={"q": query, "limit": limit, "sort": "top"}, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json().get("posts", [])
        except Exception:
            pass
        return []

    def reply(self, parent_post: Dict[str, Any], reply_text: str) -> Tuple[bool, str]:
        """
        Replies to a specific Bluesky post using official AT Protocol thread refs (root and parent).
        """
        self._reset_outcome()
        if self.dry_run:
            return self._finish(True, f"[DRY RUN] Bluesky reply simulated: {reply_text[:60]}...")
        reply_text = str(reply_text or "").strip()
        if len(reply_text) > 295:
            reply_text = reply_text[:292].rsplit(" ", 1)[0].rstrip(".,:;") + "..."
        if not reply_text:
            return self._finish(False, "Bluesky reply text is empty.")
        if not self.session:
            ok, msg = self.login()
            if not ok:
                return self._finish(False, msg)

        parent_uri = parent_post.get("uri", "")
        parent_cid = parent_post.get("cid", "")
        if not parent_uri or not parent_cid:
            return self._finish(False, "Invalid parent post details (missing uri or cid).")

        # Determine root: if the post is already a reply, use its record.reply.root, otherwise it is the root
        record_reply = parent_post.get("record", {}).get("reply", {})
        root_ref = record_reply.get("root", {"uri": parent_uri, "cid": parent_cid})

        url = "https://bsky.social/xrpc/com.atproto.repo.createRecord"
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        record: Dict[str, Any] = {
            "$type": "app.bsky.feed.post",
            "text": reply_text,
            "createdAt": now_iso,
            "reply": {
                "root": root_ref,
                "parent": {"uri": parent_uri, "cid": parent_cid}
            }
        }

        facets = detect_facets(reply_text)
        if facets:
            record["facets"] = facets

        payload = {
            "repo": self.session["did"],
            "collection": "app.bsky.feed.post",
            "record": record
        }
        headers = {
            "Authorization": f"Bearer {self.session['accessJwt']}",
            "Content-Type": "application/json"
        }
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                return self._finish(True, "Reply posted to Bluesky successfully!")
            else:
                return self._finish(False, f"Bluesky reply error: {res.text}")
        except Exception as e:
            return self._finish(False, f"Bluesky network error after submission: {e}", unknown=True)
