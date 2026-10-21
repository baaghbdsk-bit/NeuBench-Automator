import sys
import base64
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config

def export_secret():
    if not config.COOKIES_FILE.exists():
        print(f"❌ Error: {config.COOKIES_FILE} does not exist.")
        print("Please run `python main.py login` first to save your session.")
        return

    with open(config.COOKIES_FILE, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    print("\n" + "="*60)
    print("🔐 GITHUB ACTIONS SESSION SECRET")
    print("="*60)
    print("Copy the string below and save it as a Secret named:")
    print("👉 X_COOKIES_BASE64")
    print("in your GitHub Repo: Settings -> Secrets and variables -> Actions\n")
    print("-" * 60)
    print(encoded)
    print("-" * 60)
    print("\n✅ Keep this string safe and never share it publicly.\n")

if __name__ == "__main__":
    export_secret()
