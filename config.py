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
    # Window 1: Morning Commute EU / Asia Midday Standup
    "W1_MORNING_TAKE": {
        "utc_start": 4,   # 04:00 UTC = 09:30 AM IST = 00:00 EST
        "utc_end": 6,     # 06:00 UTC = 11:30 AM IST = 02:00 EST
        "ist_display": "09:30 - 11:30 IST",
        "est_display": "00:00 - 02:00 EST",
        "name": "Morning Tech Wake-Up Take",
        "primary_actions": ["post", "bluesky", "linkedin-peers", "reply"],
        "description": "Short, punchy tech take on 𝕏 and Bluesky, plus early morning engagement replies."
    },
    # Window 2: Early Evening Video Slot (5:30 PM IST / 12:00 UTC)
    "W2_YT_EVENING_EARLY": {
        "utc_start": 12,  # 12:00 UTC = 17:30 (5:30 PM) IST = 08:00 AM EST
        "utc_end": 13,    # 13:00 UTC = 18:30 (6:30 PM) IST = 09:00 AM EST
        "ist_display": "17:30 - 18:30 (5:30 PM) IST",
        "est_display": "08:00 - 09:00 AM EST",
        "name": "YouTube Shorts Evening Drop #1 (5:30 PM IST)",
        "primary_actions": ["youtube", "linkedin", "linkedin-replies", "devto"],
        "description": "First prime YouTube Short drop (5:30 PM IST) + LinkedIn & Dev.to thought leadership."
    },
    # Window 3: Peak Prime Evening Video Slot (7:30 PM IST / 14:00 UTC)
    "W3_YT_EVENING_PEAK": {
        "utc_start": 14,  # 14:00 UTC = 19:30 (7:30 PM) IST = 10:00 AM EST
        "utc_end": 15,    # 15:00 UTC = 20:30 (8:30 PM) IST = 11:00 AM EST
        "ist_display": "19:30 - 20:30 (7:30 PM) IST",
        "est_display": "10:00 - 11:00 AM EST",
        "name": "YouTube Shorts Evening Drop #2 (7:30 PM IST)",
        "primary_actions": ["youtube", "instagram", "pinterest"],
        "description": "Second prime YouTube Short drop (7:30 PM IST) + Instagram Technical Carousel & Pinterest Pin."
    },
    # Window 4: US Afternoon Break / Tech Discourse
    "W4_TECH_DEBATE": {
        "utc_start": 17,  # 17:30 UTC (17) = 23:00 PM IST = 13:30 PM EST
        "utc_end": 20,    # 20:00 UTC = 01:30 AM IST = 16:00 PM EST
        "ist_display": "23:00 - 01:30 IST",
        "est_display": "13:30 - 16:00 EST",
        "name": "Tech Debate & Viral Commentary",
        "primary_actions": ["repost", "threads", "linkedin-peers", "reply"],
        "description": "𝕏 Quote-Tweet with spicy engineering masala, Threads discussion, and sniper replies."
    },
    # Window 5: US Evening Relaxation & Mobile Feed Scroll
    "W5_EVENING_VIDEO": {
        "utc_start": 22,  # 22:00 UTC = 03:30 AM IST = 18:00 PM EST
        "utc_end": 24,    # 00:00 UTC = 05:30 AM IST = 20:00 PM EST
        "ist_display": "03:30 - 05:30 IST",
        "est_display": "18:00 - 20:00 EST",
        "name": "Prime Evening Video & Visual Pin",
        "primary_actions": ["youtube_reel", "pinterest", "linkedin-peers", "reply"],
        "description": "Evening video upload / Reel review and Pinterest graphic pin."
    }
}

# ==============================================================================
# ALGORITHMIC DAILY FREQUENCY CAPS (Guards against cannibalization & spam limits)
# ==============================================================================
CAPS_PER_PLATFORM = {
    "youtube_shorts": int(os.getenv("MAX_DAILY_YOUTUBE_SHORTS", "2")),    # 1-2/day max to prevent self-cannibalization
    "instagram_carousels": int(os.getenv("MAX_DAILY_IG_CAROUSELS", "1")), # 1 deep cheatsheet/day
    "instagram_reels": int(os.getenv("MAX_DAILY_IG_REELS", "2")),         # 1-2 reels/day
    "linkedin_posts": int(os.getenv("MAX_DAILY_LINKEDIN", "3")),          # 2-3 high-value B2B posts/day
    "linkedin_peer_comments": int(os.getenv("MAX_DAILY_LINKEDIN_PEER_COMMENTS", "0")), # 0 = Uncapped opportunity-driven (replies whenever viral post found)
    "devto_articles": int(os.getenv("MAX_DAILY_DEVTO", "1")),             # 1 comprehensive article/day
    "pinterest_pins": int(os.getenv("MAX_DAILY_PINTEREST", "3")),         # 2-3 pins/day spaced out
    "twitter_originals": int(os.getenv("MAX_DAILY_X_ORIGINALS", "4")),    # 3-4 original posts/threads
    "twitter_replies": int(os.getenv("MAX_DAILY_X_REPLIES", "16")),       # 12-16 high-signal sniper replies
    "twitter_reposts": int(os.getenv("MAX_DAILY_X_REPOSTS", "5")),        # 4-5 quote-tweets with commentary
    "threads_posts": int(os.getenv("MAX_DAILY_THREADS", "3")),            # 2-3 conversational posts
}

# Real-Time Push Alerts (Optional: Discord / Telegram)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
