import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import json
from playwright.sync_api import sync_playwright
import config

def get_linkedin_profile():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(config.LINKEDIN_USER_DATA_DIR),
            headless=True,
            channel="chrome"
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        data = {
            "name": "",
            "headline": "",
            "profile_url": "",
            "avatar_url": "",
            "connections": "",
            "impressions": ""
        }

        # Left feed card contains user info
        # Check feed identity module
        try:
            # Name & Profile link
            name_el = page.locator(".feed-identity-module__actor-meta a, .identity-headline, a[href*='/in/']").first
            if name_el:
                href = name_el.get_attribute("href") or ""
                if "/in/" in href:
                    data["profile_url"] = href if href.startswith("http") else f"https://www.linkedin.com{href}"
                raw_name = name_el.inner_text().strip().split("\n")[0]
                data["name"] = raw_name

            # Also check text in left sidebar identity widget
            widget = page.locator(".feed-identity-module, .identity-widget").first
            if widget and widget.is_visible():
                text = widget.inner_text()
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                if not data["name"] and len(lines) > 0:
                    data["name"] = lines[0]
                if len(lines) > 1:
                    data["headline"] = lines[1]
                
                # Check for connections or profile views in the widget
                for i, line in enumerate(lines):
                    if "connection" in line.lower() and i + 1 < len(lines):
                        data["connections"] = lines[i+1]
                    elif "impression" in line.lower() and i + 1 < len(lines):
                        data["impressions"] = lines[i+1]
                    elif "view" in line.lower() and i + 1 < len(lines):
                        if not data["impressions"]:
                            data["impressions"] = lines[i+1]

            # Try avatar img
            avatar_img = page.locator(".feed-identity-module img, img[alt*='Photo of'], img.evi-image").first
            if avatar_img and avatar_img.is_visible():
                data["avatar_url"] = avatar_img.get_attribute("src") or ""

        except Exception as e:
            print("Error parsing feed card:", e)

        # If profile_url is found, visit profile for richer insights
        if data.get("profile_url"):
            try:
                print("Navigating to profile URL:", data["profile_url"])
                page.goto(data["profile_url"], wait_until="domcontentloaded", timeout=25000)
                page.wait_for_timeout(2500)

                # Headline
                hl_el = page.locator(".text-body-medium.break-words, h2.top-card-layout__headline").first
                if hl_el and hl_el.is_visible():
                    data["headline"] = hl_el.inner_text().strip()

                # Avatar
                img_el = page.locator("img.evi-image.ember-view.profile-photo-edit__preview, img.pv-top-card-profile-picture__image, button img[alt*='Vivek']").first
                if img_el and img_el.is_visible():
                    data["avatar_url"] = img_el.get_attribute("src") or ""

                # Connections / Followers
                conn_el = page.locator("li.text-body-small span.t-bold, a[href*='/detail/recent-activity/'] span, ul.pv-top-card--list-bullet li").first
                for li in page.locator("ul.pv-top-card--list-bullet li, span.t-bold").all()[:6]:
                    txt = li.inner_text().strip()
                    if "connection" in txt.lower() or "follower" in txt.lower() or "+" in txt:
                        data["connections"] = txt
                        break
            except Exception as e2:
                print("Error extracting profile details:", e2)

        print("EXTRACTED LINKEDIN DATA:", json.dumps(data, indent=2))
        ctx.close()

        # Cache it in a json file so we don't have to launch browser every request
        cache_path = config.BASE_DIR / "linkedin_profile.json"
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return data

if __name__ == "__main__":
    get_linkedin_profile()
