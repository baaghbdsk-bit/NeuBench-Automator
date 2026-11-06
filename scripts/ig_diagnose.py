"""READ-ONLY Instagram session diagnostic (Phase: ig-diagnose).

Loads the saved cloud/local Instagram session, classifies authentication state
and Create-composer availability, and writes a privacy-safe JSON report.
It NEVER publishes, uploads, clicks Share, or mutates publishing history.

Exit codes:
  0  AUTHENTICATED
  1  SESSION_EXPIRED
  2  LOGIN_WALL
  3  CHECKPOINT_REQUIRED
  4  TWO_FACTOR_REQUIRED
  5  CONSENT_PROMPT
  6  UNKNOWN
  7  ERROR (script/runtime failure)
"""
import json
import os
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
COOKIE_FILE = REPO_ROOT / "instagram_session" / "cookies.json"
OUT_DIR = REPO_ROOT / "generated_visuals"
REPORT_FILE = OUT_DIR / "ig_diag_report.json"
SCREENSHOT_FILE = OUT_DIR / "ig_diag.png"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

SECRET_PATTERNS = re.compile(
    r"(sessionid|csrftoken|mid|ds_user_id|rur|datr|ig_did|"
    r"token|password|secret|auth|bearer|jwt)=[^\s;\"']{4,}",
    re.IGNORECASE,
)


def redact(text: str) -> str:
    if not text:
        return text
    return SECRET_PATTERNS.sub(lambda m: m.group(1) + "=[REDACTED]", text)


def safe_count(page, selector: str) -> int:
    try:
        return page.locator(selector).count()
    except Exception:
        return 0


def is_visible(page, selector: str, timeout_ms: int = 1500) -> bool:
    try:
        return page.locator(selector).first.is_visible(timeout=timeout_ms)
    except Exception:
        return False


def probe(page, selector: str) -> dict:
    entry = {"selector": selector, "count": 0, "visible": False, "enabled": None}
    try:
        loc = page.locator(selector)
        entry["count"] = loc.count()
        if entry["count"] > 0:
            first = loc.first
            try:
                entry["visible"] = bool(first.is_visible(timeout=1500))
            except Exception:
                entry["visible"] = False
            try:
                entry["enabled"] = bool(first.is_enabled(timeout=1500))
            except Exception:
                entry["enabled"] = None
    except Exception as ex:
        entry["error"] = f"{type(ex).__name__}: {str(ex)[:120]}"
    return entry


def classify(page) -> tuple[str, dict]:
    """Return (classification, evidence_dict). Read-only; no clicks."""
    evidence = {}

    url = ""
    title = ""
    try:
        url = page.url
    except Exception:
        url = ""
    try:
        title = page.title()
    except Exception:
        title = ""
    evidence["url"] = url
    evidence["title"] = title

    url_l = (url or "").lower()

    # --- checkpoint / challenge (positive signals) ---
    checkpoint_signals = []
    if "/challenge/" in url_l or "/checkpoint/" in url_l:
        checkpoint_signals.append("url")
    try:
        body = page.locator("body").inner_text(timeout=3000)
    except Exception:
        body = ""
    body_l = (body or "").lower()
    for phrase in ("confirm it's you", "we detected unusual activity",
                   "suspicious login", "checkpoint", "verify it's you",
                   "security code"):
        if phrase in body_l:
            checkpoint_signals.append(f"body:{phrase}")
    evidence["checkpoint_signals"] = checkpoint_signals

    # --- 2FA ---
    two_factor_signals = []
    if "/two_factor" in url_l:
        two_factor_signals.append("url")
    if safe_count(page, 'input[name="verificationCode"]') > 0:
        two_factor_signals.append("verificationCode input")
    if safe_count(page, 'input[placeholder*="code" i]') > 0 and is_visible(
            page, 'input[placeholder*="code" i]'):
        two_factor_signals.append("code placeholder input visible")
    evidence["two_factor_signals"] = two_factor_signals

    # --- session expired / login form (positive signals) ---
    login_signals = []
    if "accounts/login" in url_l:
        login_signals.append("url")
    if safe_count(page, 'input[name="username"]') > 0 and is_visible(
            page, 'input[name="username"]'):
        login_signals.append("username input visible")
    if safe_count(page, 'input[type="password"]') > 0 and is_visible(
            page, 'input[type="password"]'):
        login_signals.append("password input visible")
    if safe_count(page, 'a[href*="/accounts/login"]') > 0 and is_visible(
            page, 'a[href*="/accounts/login"]'):
        login_signals.append("login anchor visible")
    evidence["login_signals"] = login_signals

    # --- consent prompt ---
    consent_signals = []
    for sel in ('button:has-text("Allow all cookies")',
                'button:has-text("Decline optional cookies")',
                'button:has-text("Accept all")'):
        if safe_count(page, sel) > 0 and is_visible(page, sel):
            consent_signals.append(sel)
    evidence["consent_signals"] = consent_signals

    # --- authenticated indicators (positive signals) ---
    auth_signals = []
    if safe_count(page, 'svg[aria-label="Home"]') > 0:
        auth_signals.append("home svg")
    if safe_count(page, 'svg[aria-label="New post"]') > 0:
        auth_signals.append("new post svg")
    if safe_count(page, 'a[href="/direct/inbox/"]') > 0:
        auth_signals.append("inbox link")
    if safe_count(page, 'a[href*="/accounts/edit/"]') > 0:
        auth_signals.append("edit profile link")
    evidence["auth_signals"] = auth_signals

    # --- create composer probe ---
    create_probe = probe(page, 'svg[aria-label="New post"]')
    home_probe = probe(page, 'svg[aria-label="Home"]')
    evidence["create_probe"] = create_probe
    evidence["home_probe"] = home_probe

    # --- positive login-wall interstitial (rare; requires text evidence) ---
    login_wall_signals = []
    for phrase in ("log in to continue", "please log in", "log in to instagram"):
        if phrase in body_l:
            login_wall_signals.append(f"body:{phrase}")
    evidence["login_wall_signals"] = login_wall_signals

    # --- classification (priority order; absence alone never => LOGIN_WALL) ---
    if checkpoint_signals:
        return "CHECKPOINT_REQUIRED", evidence
    if two_factor_signals:
        return "TWO_FACTOR_REQUIRED", evidence
    if login_signals:
        return "SESSION_EXPIRED", evidence
    if consent_signals:
        return "CONSENT_PROMPT", evidence
    if auth_signals:
        return "AUTHENTICATED", evidence
    if login_wall_signals:
        return "LOGIN_WALL", evidence
    return "UNKNOWN", evidence


def main() -> int:
    if not COOKIE_FILE.exists():
        print("ERROR: instagram_session/cookies.json not found")
        print("DIAGNOSTIC_STATUS: ERROR")
        return 7

    try:
        raw = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
    except Exception as ex:
        print(f"ERROR: cannot parse cookie file: {type(ex).__name__}")
        print("DIAGNOSTIC_STATUS: ERROR")
        return 7

    cookies = raw.get("cookies", raw) if isinstance(raw, dict) else raw
    if not isinstance(cookies, list):
        print("ERROR: cookie file is not a list")
        print("DIAGNOSTIC_STATUS: ERROR")
        return 7

    cookie_count = len(cookies)
    # Never print values. Only count + non-sensitive metadata.
    print(f"[ig-diagnose] cookie_count={cookie_count}")
    print(f"[ig-diagnose] domains={sorted({str(c.get('domain')) for c in cookies})}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as ex:
        print(f"ERROR: playwright unavailable: {ex}")
        print("DIAGNOSTIC_STATUS: ERROR")
        return 7

    report = {
        "cookie_count": cookie_count,
        "cookie_domains": sorted({str(c.get("domain")) for c in cookies}),
        "classification": None,
        "exit_code": None,
        "evidence": None,
        "screenshot": None,
        "sanitized_body_snippet": None,
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled",
                      "--no-sandbox", "--disable-infobars"],
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=UA,
            )
            try:
                context.add_cookies(cookies)
            except Exception as ex:
                print(f"[ig-diagnose] add_cookies note: {type(ex).__name__}: {str(ex)[:120]}")

            page = context.new_page()
            try:
                page.goto("https://www.instagram.com/",
                          wait_until="domcontentloaded", timeout=40000)
            except Exception as ex:
                print(f"[ig-diagnose] navigation note: {type(ex).__name__}: {str(ex)[:120]}")
            page.wait_for_timeout(6000)

            # Dismiss cookie-consent banners (read-only, no publishing).
            for dismiss_text in ("Decline optional cookies", "Not Now"):
                try:
                    btn = page.locator(f'button:has-text("{dismiss_text}")')
                    if btn.count() > 0 and btn.first.is_visible(timeout=1000):
                        btn.first.click()
                        page.wait_for_timeout(800)
                except Exception:
                    pass

            classification, evidence = classify(page)
            report["classification"] = classification
            report["evidence"] = evidence

            # sanitized body snippet
            try:
                snippet = page.locator("body").inner_text(timeout=2000)
                snippet = (snippet or "").replace("\n", " ")[:400]
                report["sanitized_body_snippet"] = redact(snippet)
            except Exception:
                report["sanitized_body_snippet"] = None

            # create availability summary
            create_count = evidence.get("create_probe", {}).get("count", 0)
            create_visible = evidence.get("create_probe", {}).get("visible", False)
            home_count = evidence.get("home_probe", {}).get("count", 0)
            report["create_available"] = bool(create_count > 0 and create_visible)
            report["create_count"] = create_count
            report["home_count"] = home_count

            # screenshot only when necessary
            needs_screenshot = (
                classification != "AUTHENTICATED"
                or not report["create_available"]
            )
            if needs_screenshot:
                try:
                    page.screenshot(path=str(SCREENSHOT_FILE), full_page=False)
                    report["screenshot"] = str(SCREENSHOT_FILE.name)
                    print(f"[ig-diagnose] screenshot captured: {SCREENSHOT_FILE.name}")
                except Exception as ex:
                    print(f"[ig-diagnose] screenshot note: {type(ex).__name__}: {str(ex)[:120]}")
            else:
                report["screenshot"] = None

            context.close()
            browser.close()
    except Exception as ex:
        print(f"ERROR: diagnostic runtime failure: {type(ex).__name__}: {str(ex)[:200]}")
        report["classification"] = "ERROR"
        print("DIAGNOSTIC_STATUS: ERROR")
        return 7

    code_map = {
        "AUTHENTICATED": 0,
        "SESSION_EXPIRED": 1,
        "LOGIN_WALL": 2,
        "CHECKPOINT_REQUIRED": 3,
        "TWO_FACTOR_REQUIRED": 4,
        "CONSENT_PROMPT": 5,
        "UNKNOWN": 6,
    }
    exit_code = code_map.get(classification, 6)
    report["exit_code"] = exit_code

    # write report (privacy-safe)
    try:
        REPORT_FILE.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as ex:
        print(f"[ig-diagnose] report write note: {type(ex).__name__}: {str(ex)[:120]}")

    print("=" * 60)
    print(f"CLASSIFICATION: {classification}")
    print(f"AUTH_SIGNALS: {report['evidence'].get('auth_signals')}")
    print(f"LOGIN_SIGNALS: {report['evidence'].get('login_signals')}")
    print(f"CHECKPOINT_SIGNALS: {report['evidence'].get('checkpoint_signals')}")
    print(f"TWO_FACTOR_SIGNALS: {report['evidence'].get('two_factor_signals')}")
    print(f"CONSENT_SIGNALS: {report['evidence'].get('consent_signals')}")
    print(f"CREATE_COUNT: {create_count}  CREATE_VISIBLE: {create_visible}")
    print(f"HOME_COUNT: {home_count}")
    print(f"DIAGNOSTIC_STATUS: {classification}")
    print("=" * 60)
    print(f"report -> {REPORT_FILE}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
