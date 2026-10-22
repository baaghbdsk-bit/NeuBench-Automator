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

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import config
from src.tracker import ActivityTracker
from src.safety import SafetyEngine
from src.scheduler import AutomaterEngine
from src.ai_generator import AIGenerator
from src.twitter_client import TwitterClient
from src.bluesky_client import BlueskyClient

app = FastAPI(title="NeuBench-Automator", version="2.0.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Cross-Promotion: Showcase NeuBench + Connect with Us
ECOSYSTEM_PRODUCTS = [
    {
        "name": "NeuBench",
        "tagline": "Curated real-time AI news feed, LLM evaluations & 266+ frontier model benchmarks.",
        "badge": "Live Web App",
        "link": "https://neubench.vercel.app/",
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
        "platforms": {
            "x": {
                "name": "𝕏 (Twitter)",
                "configured": config.COOKIES_FILE.exists(),
                "handle": "@GWorld34864",
                "status": "connected" if config.COOKIES_FILE.exists() else "setup_needed"
            },
            "bluesky": {
                "name": "Bluesky (AT Protocol)",
                "configured": bool(config.BLUESKY_HANDLE and config.BLUESKY_APP_PASSWORD),
                "handle": config.BLUESKY_HANDLE or "Not configured",
                "status": "ready" if (config.BLUESKY_HANDLE and config.BLUESKY_APP_PASSWORD) else "setup_needed"
            },
            "linkedin": {
                "name": "LinkedIn Thought Leadership",
                "configured": config.LINKEDIN_ENABLED,
                "status": "ready"
            },
            "threads": {
                "name": "Threads Community",
                "configured": config.THREADS_ENABLED,
                "status": "ready"
            }
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

    tracker = ActivityTracker(config.BASE_DIR / "trial_metrics.json", config.BASE_DIR / "post_history.json")
    start_time = time.time()

    try:
        client = TwitterClient(headless=True, dry_run=is_dry)
        success = client.post_tweet(req.text)

        status = "success" if success else "failed"
        tracker.record_event(
            action_type="original_post",
            status=status,
            target_identifier="NeuBench Radar",
            content_preview=req.text[:80],
            skip_or_error_reason="" if success else "Playwright selector failure",
            duration_seconds=time.time() - start_time,
            is_dry_run=is_dry
        )
        return {
            "status": status,
            "dry_run": is_dry,
            "message": "Tweet published successfully!" if not is_dry else "[DRY RUN] Tweet simulated successfully."
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
        r_stories = requests.get("https://neubench.vercel.app/api/stories?limit=8", headers=headers, timeout=5)
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
                    "sourceUrl": s.get("sourceUrl", "https://neubench.vercel.app/"),
                    "neubenchUrl": f"https://neubench.vercel.app/"
                })
    except Exception as e:
        print(f"[NeuBench API] Failed to fetch stories: {e}")

    benchmarks = []
    total_models = 266
    try:
        r_bench = requests.get("https://neubench.vercel.app/api/benchmarks", headers=headers, timeout=5)
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
                    "neubenchUrl": "https://neubench.vercel.app/"
                })
    except Exception as e:
        print(f"[NeuBench API] Failed to fetch benchmarks: {e}")

    payload = {
        "status": "success",
        "hub_url": "https://neubench.vercel.app/",
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
    """Generates platform-tailored takes for 𝕏, Bluesky, LinkedIn, and Threads simultaneously."""
    try:
        ai = AIGenerator()
        inc = req.include_link if req.include_link is not None else True
        title = req.title
        summary = req.summary or ""
        company = req.company or ""

        x_take = ai.generate_neubench_take(title=title, summary=summary, company=company, include_link=inc)
        bluesky_take = ai.generate_bluesky_take(title=title, summary=summary, company=company, include_link=inc)
        linkedin_take = ai.generate_linkedin_take(title=title, summary=summary, company=company, include_link=inc)
        threads_take = ai.generate_threads_take(title=title, summary=summary, company=company, include_link=inc)

        return {
            "status": "success",
            "takes": {
                "x": x_take,
                "bluesky": bluesky_take,
                "linkedin": linkedin_take,
                "threads": threads_take
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

    tracker = ActivityTracker(config.BASE_DIR / "trial_metrics.json", config.BASE_DIR / "post_history.json")
    start_time = time.time()

    try:
        client = BlueskyClient(
            handle=config.BLUESKY_HANDLE,
            app_password=config.BLUESKY_APP_PASSWORD,
            dry_run=is_dry
        )
        success, message = client.post(req.text)
        status = "success" if success else "failed"

        tracker.record_event(
            action_type="bluesky_post",
            status=status,
            target_identifier="Bluesky (AT Protocol)",
            content_preview=req.text[:80],
            skip_or_error_reason="" if success else message,
            duration_seconds=time.time() - start_time,
            is_dry_run=is_dry
        )
        return {
            "status": status,
            "dry_run": is_dry,
            "message": message
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
