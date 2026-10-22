"""
LinkedIn Client & Helper for NeuBench-Automator.
Provides 1-click browser dispatching, formatted B2B thought-leadership generation,
and optional direct REST API publishing via LinkedIn UGC Posts API.
"""
import urllib.parse
from typing import Dict, Any, Optional, Tuple
import requests


class LinkedInClient:
    def __init__(self, access_token: str = "", author_urn: str = "", dry_run: bool = False):
        self.access_token = access_token.strip() if access_token else ""
        self.author_urn = author_urn.strip() if author_urn else ""
        self.dry_run = dry_run

    def is_api_configured(self) -> bool:
        """Checks if official LinkedIn API tokens are configured."""
        return bool(self.access_token and self.author_urn)

    def generate_share_url(self, text: str, url: str = "https://neubench.vercel.app") -> str:
        """
        Creates a 1-click LinkedIn pre-filled share URL.
        Opens the native LinkedIn web composer with pre-filled content without needing paid APIs.
        """
        encoded_text = urllib.parse.quote(text)
        encoded_url = urllib.parse.quote(url)
        # shareActive=true triggers the new post modal directly
        return f"https://www.linkedin.com/feed/?shareActive=true&text={encoded_text}"

    def post_via_api(self, text: str) -> Tuple[bool, str]:
        """
        Publishes directly to LinkedIn using the UGC Posts API (if access token is provided).
        Requires standard 'w_member_social' or 'w_organization_social' scope.
        """
        if self.dry_run:
            return True, f"[DRY RUN] LinkedIn post simulated: {text[:60]}..."

        if not self.is_api_configured():
            return False, "LinkedIn API token not configured. Use 1-click share URL or add LINKEDIN_ACCESS_TOKEN in .env."

        endpoint = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }

        payload = {
            "author": self.author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        try:
            res = requests.post(endpoint, json=payload, headers=headers, timeout=12)
            if res.status_code in (200, 201):
                post_id = res.headers.get("X-RestLi-Id", "published")
                return True, f"Successfully published to LinkedIn! (ID: {post_id})"
            else:
                return False, f"LinkedIn API returned {res.status_code}: {res.text}"
        except Exception as e:
            return False, f"LinkedIn network error: {e}"
