import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
USER_DATA_DIR = BASE_DIR / "browser_session"
COOKIES_FILE = BASE_DIR / "browser_session" / "cookies.json"

# Load environment
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

POSTS_PER_DAY = int(os.getenv("POSTS_PER_DAY", "18"))
REPLY_PERCENTAGE = int(os.getenv("REPLY_PERCENTAGE", "75"))
POST_INTERVAL_MIN_MINUTES = int(os.getenv("POST_INTERVAL_MIN_MINUTES", "35"))
POST_INTERVAL_MAX_MINUTES = int(os.getenv("POST_INTERVAL_MAX_MINUTES", "75"))

# Default high-traction niches for maximum engagement
TARGET_NICHES = [
    n.strip() for n in os.getenv(
        "TARGET_NICHES",
        "ai_tech,wealth_finance,viral_culture,work_life_debates"
    ).split(",") if n.strip()
]

# Omnichannel Expansion (Bluesky, LinkedIn, Threads)
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD", "")
LINKEDIN_ENABLED = os.getenv("LINKEDIN_ENABLED", "true").lower() in ("true", "1")
THREADS_ENABLED = os.getenv("THREADS_ENABLED", "true").lower() in ("true", "1")

