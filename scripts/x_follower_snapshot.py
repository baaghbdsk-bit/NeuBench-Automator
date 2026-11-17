"""Best-effort daily X follower snapshot using the restored browser session.

The snapshot is intentionally non-fatal: X exposes no free public follower API,
so a failed scrape is recorded as null rather than breaking the workflow.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import config

BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_FILE = BASE_DIR / "data" / "x_followers.json"
PROFILE_URL = "https://x.com/GWorld34864"


def _parse_followers(html: str):
    for pattern in (
        r'"followers_count"\s*:\s*(\d+)',
        r'aria-label="([\d,.]+\s*[KMB]?)\s+followers"',
        r'"followers"\s*:\s*(\d+)',
    ):
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(",", "").strip().upper()
            multiplier = 1
            if raw.endswith("K"):
                multiplier, raw = 1000, raw[:-1]
            elif raw.endswith("M"):
                multiplier, raw = 1_000_000, raw[:-1]
            elif raw.endswith("B"):
                multiplier, raw = 1_000_000_000, raw[:-1]
            try:
                return int(float(raw) * multiplier)
            except ValueError:
                continue
    return None


def _load_history():
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("history"), list):
            return data
    except Exception:
        pass
    return {"history": []}


def main():
    followers = None
    note = ""
    if config.COOKIES_FILE.exists():
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                context = browser.new_context(
                    storage_state=str(config.COOKIES_FILE),
                    viewport={"width": 1280, "height": 850},
                )
                page = context.new_page()
                try:
                    page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=35000)
                    page.wait_for_timeout(3000)
                    followers = _parse_followers(page.content())
                    if followers is None:
                        note = "follower count not found in profile page"
                finally:
                    context.close()
                    browser.close()
        except Exception as exc:
            note = f"snapshot failed: {type(exc).__name__}: {exc}"
    else:
        note = "browser_session/cookies.json not available"

    history = _load_history()
    history["history"].append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "followers": followers,
            "note": note,
        }
    )
    history["history"] = history["history"][-90:]
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(
        json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"[X follower snapshot] followers={followers if followers is not None else 'N/A'}"
        + (f" ({note})" if note else "")
    )


if __name__ == "__main__":
    main()
