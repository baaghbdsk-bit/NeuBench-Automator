import os

import sys

import json

import base64

import time

import subprocess

from pathlib import Path

from typing import Dict, Any, Optional, List

import requests



# Add project root to sys.path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(BASE_DIR))



# Ensure UTF-8 output on Windows consoles

if sys.platform == "win32":

    try:

        sys.stdout.reconfigure(encoding="utf-8")

        sys.stderr.reconfigure(encoding="utf-8")

    except Exception:

        pass



from fastapi import FastAPI, Request, BackgroundTasks, Query
from starlette.concurrency import run_in_threadpool
from src.trend_hunter import TrendHunter, TrendCacheManager

from fastapi.responses import HTMLResponse, JSONResponse

from fastapi.templating import Jinja2Templates

from pydantic import BaseModel



import config

from src.tracker import ActivityTracker

from src.safety import SafetyEngine

from src.scheduler import AutomaterEngine

from src.ai_generator import AIGenerator





app = FastAPI(title="NeuBench X-Post Automator", version="2.0.0")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))



# Cross-Promotion: Showcase NeuBench + Connect with Us

ECOSYSTEM_PRODUCTS = [

    {

        "name": "NeuBench",

        "tagline": "Curated real-time AI news feed, LLM evaluations & 266+ frontier model benchmarks.",

        "badge": "Live Web App",

        "link": "https://app.neubench.workers.dev/",

        "icon": "bolt",

        "cta": "Launch NeuBench"

    },

    {

        "name": "Connect on X",

        "tagline": "Follow @GWorld34864 for live creator growth, updates, direct DMs & discussions.",

        "badge": "Official X",

        "link": "https://x.com/GWorld34864",

        "icon": "brands fa-x-twitter",

        "cta": "Follow @GWorld34864"

    },

    {

        "name": "Developer Community",

        "tagline": "Star the repo, report feature requests, and build next-gen AI automation with us.",

        "badge": "GitHub",

        "link": "https://github.com/baaghbdsk-bit",

        "icon": "brands fa-github",

        "cta": "View GitHub"

    }

]



# In-memory cache for NeuBench feed (TTL: 180 seconds)

_NEUBENCH_CACHE = {

    "timestamp": 0,

    "data": None

}





# In-memory cache for live Bluesky AT Protocol metrics (TTL: 60 seconds)

_BLUESKY_METRICS_CACHE = {

    "timestamp": 0,

    "followers": 1,

    "following": 8,

    "posts": 1

}




def get_live_bluesky_metrics():

    now = time.time()

    if now - _BLUESKY_METRICS_CACHE["timestamp"] < 60:

        return _BLUESKY_METRICS_CACHE



    handle = config.BLUESKY_HANDLE or "neubench.bsky.social"

    pwd = config.BLUESKY_APP_PASSWORD

    if not (handle and pwd):

        return _BLUESKY_METRICS_CACHE



    try:

        res = requests.post(

            "https://bsky.social/xrpc/com.atproto.server.createSession",

            json={"identifier": handle, "password": pwd},

            timeout=4

        )

        if res.status_code == 200:

            jwt = res.json()["accessJwt"]

            headers = {"Authorization": f"Bearer {jwt}"}

            prof = requests.get(

                f"https://bsky.social/xrpc/app.bsky.actor.getProfile?actor={handle}",

                headers=headers,

                timeout=4

            ).json()

            _BLUESKY_METRICS_CACHE["followers"] = prof.get("followersCount", 1)

            _BLUESKY_METRICS_CACHE["following"] = prof.get("followsCount", 8)

            _BLUESKY_METRICS_CACHE["posts"] = prof.get("postsCount", 1)

            _BLUESKY_METRICS_CACHE["timestamp"] = now

    except Exception as e:

        print(f"[Bluesky Metrics] Failed to fetch: {e}")



    return _BLUESKY_METRICS_CACHE



def get_engine():

    return AutomaterEngine()



@app.get("/", response_class=HTMLResponse)

async def dashboard_home(request: Request):

    return templates.TemplateResponse(

        request=request,

        name="dashboard.html",

        context={

            "products": ECOSYSTEM_PRODUCTS,

            "profile_handle": "@GWorld34864",

            "profile_name": "vishnu rot"

        }

    )



@app.get("/api/stats")

async def get_stats():

    tracker = ActivityTracker(config.BASE_DIR / "trial_metrics.json", config.BASE_DIR / "post_history.json")

    safety = SafetyEngine()

    today_counts = tracker.get_today_counts()



    # Progress toward Monetization milestones

    current_followers = 20  # Live follower base

    target_followers = 500

    follower_pct = min(100, round((current_followers / target_followers) * 100, 1))



    # Estimated verified impressions generated so far (estimated 4.5k per successful reply/post)

    total_actions = tracker.metrics.get("lifetime_summary", {}).get("total_cycles_executed", 0)

    estimated_impressions = total_actions * 4500

    target_impressions = 5_000_000

    impression_pct = min(100, round((estimated_impressions / target_impressions) * 100, 2))



    # Calculate platform-specific activity counts from event stream

    events = tracker.metrics.get("recent_events", [])

    x_count = sum(1 for e in events if e.get("action_type") in ("original_post", "reply", "quote_tweet", "repost"))

    bsky_actions = sum(1 for e in events if "bluesky" in e.get("action_type", ""))

    linkedin_actions = sum(1 for e in events if "linkedin" in e.get("action_type", ""))



    bsky_live = get_live_bluesky_metrics()



    return {

        "profile": {

            "name": "vishnu rot",

            "handle": "@GWorld34864",

            "followers": current_followers,

            "target_followers": target_followers,

            "follower_pct": follower_pct,

            "estimated_impressions": estimated_impressions,

            "target_impressions": target_impressions,

            "impression_pct": impression_pct

        },

        "metric_transparency": {
            "x_followers": {"value": current_followers, "source": "hardcoded_constant", "status": "simulated", "last_updated": None, "is_estimated": True},
            "x_impressions": {"value": estimated_impressions, "source": "cycles_x_4500", "status": "estimated", "last_updated": None, "is_estimated": True},
            "bluesky_followers": {"value": bsky_live.get("followers", 1), "source": "bluesky_at_protocol", "status": "live", "last_updated": bsky_live.get("timestamp"), "is_estimated": False},
            "linkedin_stats": {"value": None, "source": "none", "status": "unavailable", "last_updated": None, "is_estimated": False}
        },
        "platforms": {

            "x": {

                "name": "𝕏 (Twitter)",

                "configured": config.COOKIES_FILE.exists(),

                "handle": "@GWorld34864",

                "followers": current_followers,

                "target_followers": target_followers,

                "reach": estimated_impressions,

                "total_actions": x_count,

                "status": "connected" if config.COOKIES_FILE.exists() else "setup_needed"

            },

            "bluesky": {

                "name": "Bluesky (AT Protocol)",

                "configured": bool(config.BLUESKY_HANDLE and config.BLUESKY_APP_PASSWORD),

                "handle": config.BLUESKY_HANDLE or "@neubench.bsky.social",

                "followers": bsky_live.get("followers", 1),

                "following": bsky_live.get("following", 8),

                "posts": bsky_live.get("posts", 1),

                "total_actions": bsky_actions,

                "status": "active" if (config.BLUESKY_HANDLE and config.BLUESKY_APP_PASSWORD) else "setup_needed"

            },

            "linkedin": {

                "name": "LinkedIn B2B Studio",

                "configured": config.LINKEDIN_ENABLED,

                "handle": "Professional Network",

                "target_views": 10000,

                "takes_generated": max(linkedin_actions, 1),

                "status": "ready"

            },

        },

        "today": {

            "counts": today_counts,

            "caps": {

                "original_posts": safety.max_daily_original,

                "replies": safety.max_daily_replies,

                "reposts": safety.max_daily_reposts,

                "total": safety.max_daily_total

            }

        },

        "safety": {

            "trial_enabled": safety.trial_enabled,

            "dry_run": safety.dry_run,

            "trial_max_hours": safety.trial_max_hours

        },

        "lifetime_summary": tracker.metrics.get("lifetime_summary", {}),

        "recent_events": tracker.metrics.get("recent_events", [])[-15:][::-1]  # Latest 15 first

    }



class TriggerRequest(BaseModel):

    action_type: str = "auto"

    dry_run: bool = False



@app.post("/api/action/trigger")

async def trigger_action(req: TriggerRequest, background_tasks: BackgroundTasks):

    def run_task():

        engine = AutomaterEngine(dry_run=req.dry_run)

        engine.run_single_cycle(force_action=req.action_type)



    background_tasks.add_task(run_task)

    return {"status": "queued", "message": f"Cycle triggered: {req.action_type} (Dry Run: {req.dry_run})"}



class PublishCustomRequest(BaseModel):

    text: str

    dry_run: Optional[bool] = None



@app.post("/api/action/publish-custom")

async def publish_custom_tweet(req: PublishCustomRequest):

    """Publishes a drafted tweet (e.g. from NeuBench Radar) directly or in dry run."""

    safety = SafetyEngine()

    is_dry = req.dry_run if req.dry_run is not None else safety.dry_run



    # State/event persistence is handled by AutomaterEngine for this route.

    start_time = time.time()



    try:

        engine = AutomaterEngine(dry_run=is_dry)

        success = engine.execute_x_custom_post(req.text)



        status = "success" if success else "failed"

        return {

            "status": status,

            "dry_run": is_dry,

            "message": engine.last_x_message or (
                "Tweet published successfully!" if success else "Tweet was not published."
            ),
            "duration_seconds": round(time.time() - start_time, 2)

        }

    except Exception as e:

        return {"status": "error", "message": str(e)}



@app.get("/api/neubench/feed")

async def get_neubench_feed():

    """Fetches trending AI stories and top benchmark models from NeuBench."""

    now = time.time()

    if _NEUBENCH_CACHE["data"] and (now - _NEUBENCH_CACHE["timestamp"] < 180):

        return _NEUBENCH_CACHE["data"]



    headers = {

        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    }



    stories = []

    try:

        r_stories = requests.get("https://app.neubench.workers.dev/api/stories?limit=8", headers=headers, timeout=5)

        if r_stories.status_code == 200:

            raw_stories = r_stories.json().get("stories", [])

            for s in raw_stories:

                stories.append({

                    "id": s.get("id"),

                    "title": s.get("title", ""),

                    "summary": s.get("summary", ""),

                    "company": s.get("company", "AI"),

                    "topic": s.get("topic", "News"),

                    "date": f"{s.get('month', '')} {s.get('day', '')}, {s.get('year', '')}".strip(", "),

                    "source": s.get("source", "NeuBench"),

                    "sourceUrl": s.get("sourceUrl", "https://app.neubench.workers.dev/"),

                    "neubenchUrl": f"https://app.neubench.workers.dev/"

                })

    except Exception as e:

        print(f"[NeuBench API] Failed to fetch stories: {e}")



    benchmarks = []

    total_models = 266

    try:

        r_bench = requests.get("https://app.neubench.workers.dev/api/benchmarks", headers=headers, timeout=5)

        if r_bench.status_code == 200:

            b_data = r_bench.json()

            total_models = b_data.get("count", 266)

            for m in b_data.get("models", [])[:8]:

                benchmarks_dict = m.get("benchmarks", {})

                highlight_scores = []

                for b_id, b_val in list(benchmarks_dict.items())[:3]:

                    highlight_scores.append({

                        "name": b_val.get("name", b_id),

                        "score": b_val.get("displayValue") or f"{b_val.get('score')}%"

                    })



                benchmarks.append({

                    "id": m.get("id"),

                    "name": m.get("name"),

                    "developer": m.get("developer", "AI Lab"),

                    "tagline": (m.get("tagline") or "")[:120],

                    "context": m.get("specs", {}).get("displayContext", ""),

                    "highlights": highlight_scores,

                    "neubenchUrl": "https://app.neubench.workers.dev/"

                })

    except Exception as e:

        print(f"[NeuBench API] Failed to fetch benchmarks: {e}")



    payload = {

        "status": "success",

        "hub_url": "https://app.neubench.workers.dev/",

        "total_models": total_models,

        "stories": stories,

        "benchmarks": benchmarks

    }



    _NEUBENCH_CACHE["timestamp"] = now

    _NEUBENCH_CACHE["data"] = payload

    return payload



class NeuBenchDraftRequest(BaseModel):

    title: str

    summary: Optional[str] = ""

    company: Optional[str] = ""

    include_link: Optional[bool] = True



@app.post("/api/neubench/draft")

async def draft_neubench_tweet(req: NeuBenchDraftRequest):

    """Uses Gemini to generate a sharp, contrarian, human-sounding tweet on a NeuBench AI item."""

    try:

        ai = AIGenerator()

        tweet_text = ai.generate_neubench_take(

            title=req.title,

            summary=req.summary or "",

            company=req.company or "",

            include_link=req.include_link if req.include_link is not None else True

        )

        return {

            "status": "success",

            "tweet": tweet_text,

            "char_count": len(tweet_text)

        }

    except Exception as e:

        return {"status": "error", "message": str(e)}



@app.post("/api/neubench/draft-multi")

async def draft_neubench_multi(req: NeuBenchDraftRequest):

    """Generates platform-tailored takes for 𝕏, Bluesky, and LinkedIn simultaneously."""

    try:

        ai = AIGenerator()

        inc = req.include_link if req.include_link is not None else True

        title = req.title

        summary = req.summary or ""

        company = req.company or ""



        x_take = ai.generate_neubench_take(title=title, summary=summary, company=company, include_link=inc)

        bluesky_take = ai.generate_bluesky_take(title=title, summary=summary, company=company, include_link=inc)

        linkedin_take = ai.generate_linkedin_take(title=title, summary=summary, company=company, include_link=inc)



        return {

            "status": "success",

            "takes": {

                "x": x_take,

                "bluesky": bluesky_take,

                "linkedin": linkedin_take

            }

        }

    except Exception as e:

        return {"status": "error", "message": str(e)}



class PublishBlueskyRequest(BaseModel):

    text: str

    dry_run: Optional[bool] = None



@app.post("/api/action/publish-bluesky")

async def publish_bluesky_post(req: PublishBlueskyRequest):

    """Publishes a drafted post directly to Bluesky via AT Protocol XRPC."""

    safety = SafetyEngine()

    is_dry = req.dry_run if req.dry_run is not None else safety.dry_run



    start_time = time.time()



    try:

        engine = AutomaterEngine(dry_run=is_dry)
        success = engine.execute_bluesky_custom_post(req.text)
        status = "success" if success else "failed"

        return {

            "status": status,

            "dry_run": is_dry,

            "message": engine.bluesky.last_message or (
                "Bluesky post published." if success else "Bluesky post was not published."
            ),
            "duration_seconds": round(time.time() - start_time, 2)

        }

    except Exception as e:

        return {"status": "error", "message": str(e)}



def check_linkedin_authenticated() -> bool:

    """Checks if a valid, authenticated LinkedIn session exists with li_at cookie."""

    cookie_db = config.LINKEDIN_USER_DATA_DIR / "Default" / "Network" / "Cookies"

    if not cookie_db.exists():

        return False

    try:

        import sqlite3

        uri = f"file:{cookie_db.resolve().as_posix()}?mode=ro"

        conn = sqlite3.connect(uri, uri=True)

        cur = conn.cursor()

        cur.execute("SELECT 1 FROM cookies WHERE name = 'li_at' LIMIT 1")

        row = cur.fetchone()

        conn.close()

        return row is not None

    except Exception:

        return False



_LINKEDIN_LOGIN_PROC = None

_X_LOGIN_PROC = None



@app.get("/api/auth/status")
async def get_auth_status():
    x_dir = config.USER_DATA_DIR
    x_logged_in = x_dir.exists() and any(x_dir.iterdir())
    
    li_logged_in = check_linkedin_authenticated()
    li_profile = {}
    li_profile_file = config.BASE_DIR / "linkedin_profile.json"
    if li_profile_file.exists():
        try:
            import json
            with open(li_profile_file, "r", encoding="utf-8") as f:
                li_profile = json.load(f)
        except Exception:
            pass

    bsky_configured = bool(config.BLUESKY_HANDLE and config.BLUESKY_APP_PASSWORD)
    
    bsky_metrics = get_live_bluesky_metrics()

    return {
        "x": {
            "logged_in": x_logged_in,
            "status": "Active" if x_logged_in else "Not Connected",
            "account_name": "NeuBench",
            "handle": "@GWorld34864" if x_logged_in else "Not Connected",
            "followers": "20",
            "reach": "25,000 Reach",
            "daily_quota": "Active • 28/day"
        },
        "bluesky": {
            "configured": bsky_configured,
            "logged_in": bsky_configured,
            "status": "Active" if bsky_configured else "Not Connected",
            "account_name": "NeuBench",
            "handle": config.BLUESKY_HANDLE or "neubench.bsky.social",
            "protocol": "AT Protocol XRPC",
            "reach": "Tech Dev Stream",
            "limit": "300 Chars Max"
        },
        "linkedin": {
            "logged_in": li_logged_in,
            "status": "Active" if li_logged_in else "Not Connected",
            "account_name": "NeuBench",
            "profile_url": "https://www.linkedin.com/in/vishnu-gupta-b6b2951b2/",
            "headline": "NeuBench • Tracking real-world LLM benchmarks, latency & cost",
            "location": "Bengaluru / Global",
            "connections": 8,
            "followers": 8,
            "impressions": 120,
            "profile_views": 15,
            "search_appearances": 10,
            "cadence": "Active • Omnichannel",
            "login_process_active": bool(_LINKEDIN_LOGIN_PROC and _LINKEDIN_LOGIN_PROC.poll() is None)
        }
    }

@app.post("/api/auth/launch-linkedin-login")

async def launch_linkedin_login():

    global _LINKEDIN_LOGIN_PROC

    if _LINKEDIN_LOGIN_PROC and _LINKEDIN_LOGIN_PROC.poll() is not None:

        _LINKEDIN_LOGIN_PROC = None



    script_path = config.BASE_DIR / "scripts" / "login_linkedin.py"

    venv_py = config.BASE_DIR / "venv" / "Scripts" / "python.exe"

    py_bin = str(venv_py) if venv_py.exists() else sys.executable



    creation_flags = 0

    if sys.platform == "win32":

        creation_flags = subprocess.CREATE_NEW_CONSOLE



    try:

        if not (_LINKEDIN_LOGIN_PROC and _LINKEDIN_LOGIN_PROC.poll() is None):

            _LINKEDIN_LOGIN_PROC = subprocess.Popen(

                [py_bin, str(script_path)],

                cwd=str(config.BASE_DIR),

                creationflags=creation_flags

            )

    except Exception:

        pass



    return {

        "status": "launched",

        "message": "Login helper initiated! If the Chrome window does not appear on your desktop, run 'python main.py login-linkedin' in your command prompt.",

        "command": "python main.py login-linkedin"

    }




@app.post("/api/auth/launch-x-login")

async def launch_x_login():

    global _X_LOGIN_PROC

    if _X_LOGIN_PROC and _X_LOGIN_PROC.poll() is None:

        return {"status": "already_running", "message": "𝕏 login browser is already open on your desktop."}

    

    script_path = config.BASE_DIR / "scripts" / "login_browser.py"

    _X_LOGIN_PROC = subprocess.Popen(

        [sys.executable, str(script_path)],

        cwd=str(config.BASE_DIR)

    )

    return {

        "status": "launched",

        "message": "Browser opened! Please log into 𝕏 in the window that just appeared on your screen."

    }




_AUTOPILOT_PROC = None

@app.get("/api/autopilot/status")
async def get_autopilot_status():
    global _AUTOPILOT_PROC
    is_running = False
    if _AUTOPILOT_PROC and _AUTOPILOT_PROC.poll() is None:
        is_running = True
    else:
        try:
            res = subprocess.run(
                ["powershell", "-Command", "Get-CimInstance Win32_Process -Filter \"CommandLine LIKE '%main.py start%'\" | Select-Object -ExpandProperty ProcessId"],
                capture_output=True, text=True, timeout=3
            )
            pids = res.stdout.strip().split()
            if pids and any(p.isdigit() for p in pids):
                is_running = True
        except Exception:
            pass
    return {
        "running": is_running,
        "status": "Autopilot Active (24/7)" if is_running else "Autopilot Idle",
        "interval_minutes": "25 - 50 mins",
        "platforms": ["𝕏", "Bluesky", "LinkedIn"]
    }

@app.post("/api/autopilot/toggle")
async def toggle_autopilot():
    global _AUTOPILOT_PROC
    status_info = await get_autopilot_status()
    if status_info["running"]:
        try:
            subprocess.run(
                ["powershell", "-Command", "Get-CimInstance Win32_Process -Filter \"CommandLine LIKE '%main.py start%'\" | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
                timeout=5
            )
            if _AUTOPILOT_PROC:
                try:
                    _AUTOPILOT_PROC.terminate()
                except Exception:
                    pass
            _AUTOPILOT_PROC = None
            return {"success": True, "running": False, "message": "24/7 Autopilot paused successfully."}
        except Exception as e:
            return {"success": False, "running": True, "message": f"Error stopping: {e}"}
    else:
        try:
            venv_py = config.BASE_DIR / "venv" / "Scripts" / "python.exe"
            py_bin = str(venv_py) if venv_py.exists() else sys.executable
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            _AUTOPILOT_PROC = subprocess.Popen(
                [py_bin, "-u", "main.py", "start"],
                cwd=str(config.BASE_DIR),
                creationflags=creation_flags
            )
            return {"success": True, "running": True, "message": "24/7 Autopilot active! Posting across all 5 platforms automatically."}
        except Exception as e:
            return {"success": False, "running": False, "message": f"Error starting: {e}"}

@app.post("/api/action/publish-omnichannel")
async def publish_omnichannel_endpoint(payload: Optional[Dict[str, Any]] = None):
    """Publishes a synchronized AI benchmark take across all 5 platforms with NeuBench backlinks."""
    try:
        from src.scheduler import AutomaterEngine
        engine = AutomaterEngine(dry_run=False)
        ok = engine.run_single_cycle(force_action="post")
        return {
            "success": ok,
            "message": "Omnichannel broadcast published across all 5 platforms with https://app.neubench.workers.dev!"
        }
    except Exception as e:
        return {"success": False, "message": f"Omnichannel publish error: {e}"}


class PublishLinkedInRequest(BaseModel):

    text: str



@app.post("/api/action/publish-linkedin")
async def publish_linkedin_action(req: PublishLinkedInRequest):
    from src.scheduler import AutomaterEngine

    try:
        engine = AutomaterEngine(dry_run=False)
        ok = engine.execute_linkedin_custom_post(req.text)
        return {
            "status": "success" if ok else "failed",
            "message": "LinkedIn post completed by the guarded automation path." if ok else "LinkedIn post was not sent; see the automation log for the guard or error reason.",
        }
    except Exception as error:
        return {"status": "failed", "message": f"LinkedIn publish error: {error}"}


@app.post("/api/action/follow-linkedin-network")
async def follow_linkedin_network_endpoint(background_tasks: BackgroundTasks):
    """Triggers background follow of top AI leaders on LinkedIn."""
    def run_follower():
        try:
            from scripts.follow_linkedin_ai_network import follow_top_network
            follow_top_network(max_count=35, headless=True)
        except Exception as e:
            print(f"[LinkedIn Follower Error] {e}")
            
    background_tasks.add_task(run_follower)
    return {"success": True, "message": "Started following top AI leaders and organizations in background!"}

class SettingsRequest(BaseModel):

    max_daily_total: Optional[int] = 20

    max_daily_replies: Optional[int] = 14

    dry_run: Optional[bool] = False

    target_niches: Optional[str] = "ai_tech,wealth_finance,viral_culture"

    bluesky_handle: Optional[str] = None

    bluesky_app_password: Optional[str] = None



@app.post("/api/settings")

async def update_settings(req: SettingsRequest):

    env_file = config.BASE_DIR / ".env"

    lines = []

    if env_file.exists():

        with open(env_file, "r", encoding="utf-8") as f:

            lines = f.readlines()



    updates = {

        "MAX_DAILY_TOTAL": str(req.max_daily_total),

        "MAX_DAILY_REPLIES": str(req.max_daily_replies),

        "DRY_RUN": "true" if req.dry_run else "false",

        "TARGET_NICHES": req.target_niches

    }

    if req.bluesky_handle is not None:

        updates["BLUESKY_HANDLE"] = req.bluesky_handle.strip()

        config.BLUESKY_HANDLE = req.bluesky_handle.strip()

    if req.bluesky_app_password is not None:

        updates["BLUESKY_APP_PASSWORD"] = req.bluesky_app_password.strip()

        config.BLUESKY_APP_PASSWORD = req.bluesky_app_password.strip()



    new_lines = []

    seen = set()

    for line in lines:

        if "=" in line and not line.strip().startswith("#"):

            k = line.split("=")[0].strip()

            if k in updates:

                new_lines.append(f"{k}={updates[k]}\n")

                seen.add(k)

                continue

        new_lines.append(line)



    for k, v in updates.items():

        if k not in seen:

            new_lines.append(f"{k}={v}\n")



    with open(env_file, "w", encoding="utf-8") as f:

        f.writelines(new_lines)



    return {"status": "success", "message": "Settings updated successfully"}





AVAILABLE_TOPICS = [

    {

        "id": "ai_benchmarks",

        "name": "AI Models and Benchmarks",

        "icon": "fa-solid fa-microchip",

        "desc": "Frontier LLM evaluations, latency, MMLU and reasoning scores from NeuBench",

        "best_for": ["x", "bluesky"]

    },

    {

        "id": "contrarian_takes",

        "name": "Contrarian Hot Takes",

        "icon": "fa-solid fa-fire-flame-curved",

        "desc": "Calling out tech myths, overhyped trends, and bold unpopular predictions",

        "best_for": ["x"]

    },

    {

        "id": "tech_culture",

        "name": "Work and City Culture",

        "icon": "fa-solid fa-mug-hot",

        "desc": "Bengaluru potholes, startup hustle satire, corporate irony and developer life",

        "best_for": ["x"]

    },

    {

        "id": "open_source",

        "name": "Open-Source and AT Protocol",

        "icon": "fa-brands fa-git-alt",

        "desc": "Decentralized social networks, open weights, local models and developer tooling",

        "best_for": ["bluesky"]

    },

    {

        "id": "b2b_thought_leadership",

        "name": "B2B Thought Leadership",

        "icon": "fa-solid fa-briefcase",

        "desc": "Enterprise AI ROI, team architecture, productivity and strategic engineering",

        "best_for": ["linkedin"]

    },

    {

        "id": "market_finance",

        "name": "Markets and Wealth Culture",

        "icon": "fa-solid fa-chart-line",

        "desc": "Tech equity, funding rounds, compensation realities and market macro",

        "best_for": ["x", "linkedin"]

    },

    {

        "id": "community_discussions",

        "name": "Community Questions and Polls",

        "icon": "fa-solid fa-comments",

        "desc": "Open-ended prompts asking developers and creators for their honest workflows",

        "best_for": ["x"]

    }

]



DEFAULT_TOPIC_ROUTING = {

    "x": ["ai_benchmarks", "contrarian_takes", "tech_culture", "market_finance"],

    "bluesky": ["ai_benchmarks", "open_source"],

    "linkedin": ["ai_benchmarks", "b2b_thought_leadership", "market_finance"]

}



def get_topic_routing() -> dict:

    fpath = config.BASE_DIR / "topic_routing.json"

    if fpath.exists():

        try:

            import json

            with open(fpath, "r", encoding="utf-8") as f:

                return json.load(f)

        except Exception:

            pass

    return DEFAULT_TOPIC_ROUTING



def save_topic_routing(routing: dict):

    fpath = config.BASE_DIR / "topic_routing.json"

    import json

    with open(fpath, "w", encoding="utf-8") as f:

        json.dump(routing, f, indent=2)



@app.get("/api/topics")

async def get_topics_api():

    return {

        "available_topics": AVAILABLE_TOPICS,

        "routing": get_topic_routing()

    }



class TopicRoutingUpdateRequest(BaseModel):

    routing: Dict[str, List[str]]



@app.post("/api/topics")

async def update_topics_api(req: TopicRoutingUpdateRequest):

    save_topic_routing(req.routing)

    return {"status": "success", "message": "Topic routing updated successfully", "routing": req.routing}


# ==============================================================================
# TREND INTELLIGENCE ROUTES (PHASE 2B)
# ==============================================================================

_trend_hunter_instance: Optional[TrendHunter] = None

def get_trend_hunter() -> TrendHunter:
    global _trend_hunter_instance
    if _trend_hunter_instance is None:
        _trend_hunter_instance = TrendHunter()
    return _trend_hunter_instance


class TrendRefreshRequest(BaseModel):
    geo: Optional[str] = "IN"
    background: Optional[bool] = False
    limit: Optional[int] = 20


@app.get("/api/trends")
async def get_trends_api(
    platform: Optional[str] = Query(None, description="Target platform filter (x, linkedin, bluesky)"),
    category: Optional[str] = Query(None, description="Topical category filter (ai_tech, breaking_news, frontier_paper, etc.)"),
    include_sensitive: bool = Query(True, description="Whether to include sensitive topics requiring approval"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of trends to return"),
    auto_refresh: bool = Query(False, description="Automatically trigger live fetch if cache is empty")
):
    """
    Returns normalized, deduplicated, and deterministically ranked trends from cache.
    Non-blocking execution via run_in_threadpool.
    """
    try:
        hunter = get_trend_hunter()

        def _fetch_trends():
            cached_data = hunter.cache.load_cache()
            trends = cached_data.get("trends", [])

            if not trends and auto_refresh:
                trends = hunter.get_curated_trending_topics(use_cache=False, refresh=True)
                cached_data = hunter.cache.load_cache()

            total_cached = len(trends)
            metadata = cached_data.get("metadata", {})
            last_updated = metadata.get("last_updated")

            platform_norm = (platform or "").lower().strip()
            cat_norm = (category or "").lower().strip()

            filtered = []
            for t in trends:
                if not include_sensitive and t.get("is_sensitive", False):
                    continue

                item_cat = (t.get("category") or "").lower().strip()
                if cat_norm:
                    if cat_norm not in item_cat and item_cat not in cat_norm:
                        continue
                elif platform_norm in ("linkedin", "bluesky"):
                    if item_cat not in ("ai_tech", "frontier_paper", "explainer"):
                        continue

                filtered.append(t)
                if len(filtered) >= limit:
                    break

            return {
                "status": "success",
                "count": len(filtered),
                "total_cached": total_cached,
                "last_updated": last_updated,
                "filters": {
                    "platform": platform_norm or None,
                    "category": cat_norm or None,
                    "include_sensitive": include_sensitive,
                    "limit": limit
                },
                "trends": filtered
            }

        result = await run_in_threadpool(_fetch_trends)
        return JSONResponse(status_code=200, content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to retrieve trends: {str(e)}",
                "count": 0,
                "total_cached": 0,
                "trends": []
            }
        )


@app.post("/api/trends/refresh")
async def refresh_trends_api(
    background_tasks: BackgroundTasks,
    req: Optional[TrendRefreshRequest] = None
):
    """
    Triggers live trend collection, normalization, deduplication, ranking, and persistence.
    Can be run synchronously in threadpool or deferred to background tasks.
    """
    request_data = req or TrendRefreshRequest()
    hunter = get_trend_hunter()

    def _execute_refresh():
        try:
            return hunter.get_curated_trending_topics(use_cache=False, refresh=True)
        except Exception as err:
            print(f"[TrendHunter API] Refresh error: {err}")
            return []

    try:
        if request_data.background:
            background_tasks.add_task(_execute_refresh)
            return JSONResponse(
                status_code=202,
                content={
                    "status": "accepted",
                    "message": "Trend collection initiated in background.",
                    "background": True
                }
            )
        else:
            refreshed = await run_in_threadpool(_execute_refresh)
            limit = request_data.limit or 20
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Trends collected and cache updated successfully.",
                    "total_refreshed": len(refreshed),
                    "count": min(len(refreshed), limit),
                    "trends": refreshed[:limit]
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Trend refresh failed: {str(e)}",
                "trends": []
            }
        )





class RecordCopyRequest(BaseModel):

    platform: str

    content_preview: Optional[str] = ""



@app.post("/api/action/record-copy")

async def record_copy(req: RecordCopyRequest):

    """Records copy action to track engagement metrics for non-API platforms."""

    tracker = ActivityTracker(config.BASE_DIR / "trial_metrics.json", config.BASE_DIR / "post_history.json")

    tracker.record_event(

        action_type=f"{req.platform}_copy",

        status="success",

        target_identifier=f"{req.platform.upper()} Studio",

        content_preview=req.content_preview[:80],

        duration_seconds=0.1,

        is_dry_run=False

    )

    return {"status": "success", "platform": req.platform}


@app.get("/api/products")

async def get_ecosystem_products():

    return {"products": ECOSYSTEM_PRODUCTS}



class CloudDeployRequest(BaseModel):

    repo_name: Optional[str] = "X-Post-Automater"

    is_private: Optional[bool] = True



@app.post("/api/cloud-deploy")

async def cloud_deploy(req: CloudDeployRequest):

    """Bridges Option B with Option C by automating GitHub Actions setup."""

    try:

        # Check if gh CLI is authenticated

        auth_check = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)

        if auth_check.returncode != 0:

            return {

                "status": "manual_required",

                "message": "GitHub CLI not logged in locally. Please follow the 3-step guide in README to configure GitHub Secrets."

            }



        # Export session cookies base64

        cookies_file = config.COOKIES_FILE

        if not cookies_file.exists():

            return {"status": "error", "message": "No login session found. Run login first."}



        with open(cookies_file, "rb") as f:

            cookies_b64 = base64.b64encode(f.read()).decode("utf-8")



        # Set GitHub secret for GEMINI_API_KEY

        if config.GEMINI_API_KEY:

            subprocess.run(

                ["gh", "secret", "set", "GEMINI_API_KEY", "-b", config.GEMINI_API_KEY],

                check=True,

                capture_output=True

            )



        # Set GitHub secret for X_COOKIES_BASE64

        subprocess.run(

            ["gh", "secret", "set", "X_COOKIES_BASE64"],

            input=cookies_b64,

            text=True,

            check=True,

            capture_output=True

        )



        # Trigger workflow run

        subprocess.run(

            ["gh", "workflow", "run", "x_automater.yml"],

            check=True,

            capture_output=True

        )



        return {

            "status": "success",

            "message": "24/7 Cloud Engine deployed and triggered successfully on your GitHub account!"

        }

    except Exception as e:

        return {"status": "error", "message": f"Deployment error: {e}"}
