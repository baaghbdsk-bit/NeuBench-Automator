import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent
USER_DATA_DIR = BASE_DIR / "browser_session"
COOKIES_FILE = BASE_DIR / "browser_session" / "cookies.json"
LINKEDIN_USER_DATA_DIR = BASE_DIR / "linkedin_session"

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

# Omnichannel Expansion (Bluesky, LinkedIn, Threads, Instagram, Dev.to, Pinterest, YouTube)
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD", "")
LINKEDIN_ENABLED = os.getenv("LINKEDIN_ENABLED", "true").lower() in ("true", "1")
LINKEDIN_ORGANIZATION_URN = os.getenv("LINKEDIN_ORGANIZATION_URN", "")
THREADS_ENABLED = os.getenv("THREADS_ENABLED", "true").lower() in ("true", "1")
INSTAGRAM_ENABLED = os.getenv("INSTAGRAM_ENABLED", "true").lower() in ("true", "1")
DEVTO_API_KEY = os.getenv("DEVTO_API_KEY", "")
DEVTO_ENABLED = os.getenv("DEVTO_ENABLED", "true").lower() in ("true", "1")
PINTEREST_ENABLED = os.getenv("PINTEREST_ENABLED", "true").lower() in ("true", "1")
YOUTUBE_ENABLED = os.getenv("YOUTUBE_ENABLED", "true").lower() in ("true", "1")

# ==============================================================================
# ALGORITHMIC TIME-SLOT DISTRIBUTION MATRIX (Global Developer & Tech Audience)
# Time zones balanced for: US West Coast (PST), US East Coast (EST), Europe (GMT/CET), India (IST)
# ==============================================================================

ALGORITHMIC_WINDOWS = {
    # Slot 1: 9:00 AM IST (03:30 UTC) - Morning Tech Kickoff & Architecture Drop
    "W1_MORNING_KICKOFF": {
        "utc_start": 3,   # 03:00 - 04:30 UTC = 08:30 - 10:00 AM IST
        "utc_end": 5,
        "ist_display": "08:30 - 10:00 AM IST (Target 9:00 AM IST)",
        "est_display": "23:00 - 00:30 EST",
        "name": "Morning Kickoff & AI Architecture Drop",
        "primary_actions": ["linkedin", "post", "bluesky", "reply"],
        "description": "9:00 AM IST LinkedIn drop with custom animated technical visual, plus cross-platform morning thoughts."
    },
    # Slot 2: 1:00 PM IST (07:30 UTC) - Midday Engineering Masterclass
    "W2_MIDDAY_ENGINEERING": {
        "utc_start": 7,   # 07:00 - 08:30 UTC = 12:30 - 02:00 PM IST
        "utc_end": 9,
        "ist_display": "12:30 - 02:00 PM IST (Target 1:00 PM IST)",
        "est_display": "02:30 - 04:00 AM EST / 08:30 - 10:00 AM CET",
        "name": "Midday Engineering Masterclass & Benchmark Race",
        "primary_actions": ["linkedin", "threads", "linkedin-replies", "devto"],
        "description": "1:00 PM IST LinkedIn drop with dynamic benchmark or code breakdown, European work hours launch."
    },
    # Slot 3: 5:00 PM IST (11:30 UTC) - Evening Transition & YouTube Drop
    "W3_EVENING_TRANSITION": {
        "utc_start": 11,  # 11:00 - 12:30 UTC = 04:30 - 06:00 PM IST
        "utc_end": 13,
        "ist_display": "04:30 - 06:00 PM IST (Target 5:00 PM IST)",
        "est_display": "06:30 - 08:00 AM EST (US East Standup)",
        "name": "Evening Transition & Video Drop",
        "primary_actions": ["linkedin", "youtube", "pinterest", "reply"],
        "description": "5:00 PM IST LinkedIn drop targeting US East early risers & India evening commute + YouTube Short."
    },
    # Slot 4: 9:00 PM IST (15:30 UTC) - Prime US Midday & India Evening Peak
    "W4_PRIME_DISCOURSE": {
        "utc_start": 15,  # 15:00 - 16:30 UTC = 08:30 - 10:00 PM IST
        "utc_end": 17,
        "ist_display": "08:30 - 10:00 PM IST (Target 9:00 PM IST)",
        "est_display": "10:30 - 12:00 PM EST (US Peak Hours)",
        "name": "Peak US Prime Discourse & Technical Blueprint",
        "primary_actions": ["linkedin", "repost", "instagram", "threads"],
        "description": "9:00 PM IST LinkedIn post hitting peak US business hours with custom technical blueprint."
    },
    # Slot 5: 12:00 AM (Midnight) IST (18:30 UTC) - Silicon Valley Afternoon / Midnight Drop
    "W5_MIDNIGHT_SV_DROP": {
        "utc_start": 18,  # 18:00 - 19:30 UTC = 11:30 PM - 01:00 AM IST
        "utc_end": 20,
        "ist_display": "11:30 PM - 01:00 AM IST (Target 12:00 AM IST)",
        "est_display": "13:30 - 15:00 EST / 10:30 - 12:00 PST (SF Peak)",
        "name": "Silicon Valley Peak & Midnight AI Architecture Drop",
        "primary_actions": ["linkedin", "linkedin-peers", "bluesky", "reply"],
        "description": "12:00 AM IST LinkedIn post maximizing Silicon Valley/PST lunchtime and afternoon tech feeds."
    }
}

# ==============================================================================
# ALGORITHMIC DAILY FREQUENCY CAPS (Guards against cannibalization & spam limits)
# ==============================================================================
CAPS_PER_PLATFORM = {
    "youtube_shorts": int(os.getenv("MAX_DAILY_YOUTUBE_SHORTS", "2")),    # 1-2/day max to prevent self-cannibalization
    "instagram_carousels": int(os.getenv("MAX_DAILY_IG_CAROUSELS", "1")), # 1 deep cheatsheet/day
    "instagram_reels": int(os.getenv("MAX_DAILY_IG_REELS", "2")),         # 1-2 reels/day
    "linkedin_posts": int(os.getenv("MAX_DAILY_LINKEDIN", "5")),          # 5 targeted posts/day at 9AM, 1PM, 5PM, 9PM, 12AM IST
    "linkedin_peer_comments": int(os.getenv("MAX_DAILY_LINKEDIN_PEER_COMMENTS", "0")), # 0 = Uncapped opportunity-driven (replies whenever viral post found)
    "devto_articles": int(os.getenv("MAX_DAILY_DEVTO", "1")),             # 1 comprehensive article/day
    "pinterest_pins": int(os.getenv("MAX_DAILY_PINTEREST", "3")),         # 2-3 pins/day spaced out
    "twitter_originals": int(os.getenv("MAX_DAILY_X_ORIGINALS", "8")),    # 6-8 original posts spaced across active windows
    "twitter_replies": int(os.getenv("MAX_DAILY_X_REPLIES", "24")),       # 20-25 high-signal sniper replies on viral tweets
    "twitter_reposts": int(os.getenv("MAX_DAILY_X_REPOSTS", "6")),        # 5-6 quote-tweets with commentary
    "threads_posts": int(os.getenv("MAX_DAILY_THREADS", "5")),            # 4-5 conversational posts
    "bluesky_posts": int(os.getenv("MAX_DAILY_BLUESKY", "6")),            # 5-6 tech takes
}

# Real-Time Push Alerts (Optional: Discord / Telegram)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
