import os
import sys
import json
import base64
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

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

app = FastAPI(title="X-Post-Automater Dashboard", version="1.0.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# Cross-Promotion: Showcase NeuBench + Connect with Us
ECOSYSTEM_PRODUCTS = [
    {
        "name": "NeuBench",
        "tagline": "Curated real-time AI news feed, LLM evaluations & frontier model benchmarks.",
        "badge": "Live Web App",
        "link": "https://neubench.vercel.app/",
        "icon": "bolt",
        "cta": "Launch NeuBench"
    },
    {
        "name": "Connect on X",
        "tagline": "Follow @GWorld34864 for growth updates, discussions, feature requests & direct DMs.",
        "badge": "Official X",
        "link": "https://x.com/GWorld34864",
        "icon": "brands fa-x-twitter",
        "cta": "Connect on X"
    },
    {
        "name": "Developer Community",
        "tagline": "Star our repository, report issues, and collaborate with us on next-gen AI tools.",
        "badge": "GitHub",
        "link": "https://github.com/baaghbdsk-bit",
        "icon": "brands fa-github",
        "cta": "View GitHub"
    }
]

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

    # Estimated verified impressions generated so far (estimated 5k per successful reply/post)
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

class SettingsRequest(BaseModel):
    max_daily_total: Optional[int] = 20
    max_daily_replies: Optional[int] = 14
    dry_run: Optional[bool] = False
    target_niches: Optional[str] = "ai_tech,wealth_finance,viral_culture"

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

