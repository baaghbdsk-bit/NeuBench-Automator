from pathlib import Path

app_path = Path("src/web/app.py")
content = app_path.read_text(encoding="utf-8")

auth_code = '''
_LINKEDIN_LOGIN_PROC = None
_X_LOGIN_PROC = None

@app.get("/api/auth/status")
async def get_auth_status():
    x_dir = config.USER_DATA_DIR
    x_logged_in = x_dir.exists() and any(x_dir.iterdir())
    
    li_dir = config.LINKEDIN_USER_DATA_DIR
    li_logged_in = li_dir.exists() and any(li_dir.iterdir())
    
    bsky_configured = bool(config.BLUESKY_HANDLE and config.BLUESKY_APP_PASSWORD)
    
    return {
        "x": {
            "logged_in": x_logged_in,
            "handle": "@GWorld34864" if x_logged_in else "Not Connected"
        },
        "linkedin": {
            "logged_in": li_logged_in,
            "login_process_active": bool(_LINKEDIN_LOGIN_PROC and _LINKEDIN_LOGIN_PROC.poll() is None)
        },
        "bluesky": {
            "configured": bsky_configured,
            "handle": config.BLUESKY_HANDLE or "neubench.bsky.social"
        }
    }

@app.post("/api/auth/launch-linkedin-login")
async def launch_linkedin_login():
    global _LINKEDIN_LOGIN_PROC
    if _LINKEDIN_LOGIN_PROC and _LINKEDIN_LOGIN_PROC.poll() is None:
        return {"status": "already_running", "message": "LinkedIn login browser is already open on your desktop."}
    
    script_path = config.BASE_DIR / "scripts" / "login_linkedin.py"
    _LINKEDIN_LOGIN_PROC = subprocess.Popen(
        [sys.executable, str(script_path)],
        cwd=str(config.BASE_DIR)
    )
    return {
        "status": "launched",
        "message": "Browser opened! Please log into LinkedIn in the window that just appeared on your screen."
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

class PublishLinkedInRequest(BaseModel):
    text: str

@app.post("/api/action/publish-linkedin")
async def publish_linkedin_action(req: PublishLinkedInRequest):
    from src.linkedin_automater import LinkedInAutomater
    automater = LinkedInAutomater(headless=True, dry_run=False)
    if not automater.is_session_available():
        return {"status": "not_logged_in", "message": "Please connect your LinkedIn account first."}
    
    ok, msg = automater.post(req.text)
    status = "success" if ok else "failed"
    tracker.record_event(
        action_type="linkedin_post",
        status=status,
        target_identifier="LinkedIn B2B",
        content_preview=req.text[:80],
        skip_or_error_reason="" if ok else msg,
        duration_seconds=4.0,
        is_dry_run=False
    )
    return {"status": status, "message": msg}
'''

if "/api/auth/launch-linkedin-login" not in content:
    target = '    except Exception as e:\n        return {"status": "error", "message": str(e)}\n\nclass SettingsRequest(BaseModel):'
    replacement = '    except Exception as e:\n        return {"status": "error", "message": str(e)}\n' + auth_code + '\nclass SettingsRequest(BaseModel):'
    content = content.replace(target, replacement)
    app_path.write_text(content, encoding="utf-8")
    print("Patched src/web/app.py with auth endpoints!")
else:
    print("Auth endpoints already present.")
