import os
import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Scopes needed for YouTube video upload and caption management
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
        print("\nTo setup YouTube API:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
        print("2. Create a project and enable 'YouTube Data API v3'")
        print("3. Go to 'APIs & Services' -> 'Credentials' -> 'Create Credentials' -> 'OAuth client ID'")
        print("4. Application type: 'Desktop app'")
        print("5. Download the JSON, rename it to 'client_secret.json' and place it in the project root directory:")
        print(f"   {CLIENT_SECRETS_FILE}")
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
            print("[YouTube Auth] Initiating browser OAuth consent flow...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
        print(f"[YouTube Auth] Saved authorized credentials to: {TOKEN_FILE}")

    print("[YouTube Auth] Logged in successfully!")
    return True

if __name__ == "__main__":
    login_youtube()
