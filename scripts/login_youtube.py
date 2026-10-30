import os
import sys
import subprocess
from pathlib import Path

# Auto-switch to virtual environment Python if invoked via global python
_BASE_DIR = Path(__file__).resolve().parent.parent
_VENV_PYTHON = _BASE_DIR / "venv" / "Scripts" / "python.exe"
if _VENV_PYTHON.exists() and Path(sys.executable).resolve() != _VENV_PYTHON.resolve():
    try:
        sys.exit(subprocess.call([str(_VENV_PYTHON)] + sys.argv))
    except Exception:
        pass

# Ensure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtubepartner"
]

BASE_DIR = Path(__file__).resolve().parent.parent
CLIENT_SECRETS_FILE = BASE_DIR / "client_secret.json"
TOKEN_FILE = BASE_DIR / "youtube_token.json"

def login_youtube():
    if not CLIENT_SECRETS_FILE.exists():
        print(f"\n[ERROR] '{CLIENT_SECRETS_FILE.name}' not found in {BASE_DIR}!")
        return False

    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[YouTube Auth] Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("\n[YouTube Auth] Starting local OAuth authorization server...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(port=8088, open_browser=True)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
        print(f"\n[YouTube Auth] ✅ Saved authorized credentials to: {TOKEN_FILE}")

    print("[YouTube Auth] ✅ Logged in successfully!")
    return True

if __name__ == "__main__":
    login_youtube()
