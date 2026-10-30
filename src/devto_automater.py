import os
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Tuple
import config

class DevToAutomater:
    """Publishes educational technical articles and 90-day AI lessons to Dev.to (@neubench)."""

    BASE_URL = "https://dev.to/api/articles"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.DEVTO_API_KEY

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def create_article(
        self,
        title: str,
        body_markdown: str,
        tags: list[str] = None,
        series: str = "AI Explained: Zero to Advanced",
        published: bool = True,
        canonical_url: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Publishes a markdown article to Dev.to.
        Returns: (success: bool, message: str, article_url: Optional[str])
        """
        if not self.is_configured():
            return False, "DEVTO_API_KEY is not configured.", None

        if tags is None:
            tags = ["ai", "machinelearning", "programming", "datascience"]
        # Dev.to accepts max 4 tags, lowercase alphanumeric only
        cleaned_tags = [t.lower().replace("-", "").replace("_", "")[:30] for t in tags[:4]]

        payload = {
            "article": {
                "title": title,
                "body_markdown": body_markdown,
                "published": published,
                "tags": cleaned_tags,
                "series": series
            }
        }
        if canonical_url:
            payload["article"]["canonical_url"] = canonical_url

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.BASE_URL,
            data=data_bytes,
            headers={
                "api-key": self.api_key,
                "Content-Type": "application/json",
                "User-Agent": "NeuBenchAutomater/1.0"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                article_url = res_data.get("url") or res_data.get("canonical_url", "")
                print(f"[DevToAutomater] ✅ Successfully published article: {article_url}")
                return True, "Published to Dev.to", article_url
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            print(f"[DevToAutomater] ❌ HTTP error {e.code}: {error_body}")
            return False, f"Dev.to HTTP {e.code}: {error_body}", None
        except Exception as e:
            print(f"[DevToAutomater] ❌ Error: {e}")
            return False, f"Dev.to error: {e}", None
