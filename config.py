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
        "primary_actions": ["post", "bluesky", "reply"],
        "description": "Short, punchy tech take on 𝕏 and Bluesky, plus early morning engagement replies."
    },
    # Window 2: Europe Afternoon / US Pre-Standup
    "W2_B2B_LONGFORM": {
        "utc_start": 11,  # 11:00 UTC = 16:30 PM IST = 07:00 AM EST
        "utc_end": 13,    # 13:00 UTC = 18:30 PM IST = 09:00 AM EST
        "ist_display": "16:30 - 18:30 IST",
        "est_display": "07:00 - 09:00 EST",
        "name": "B2B Thought-Leadership & Engineering Deep-Dive",
        "primary_actions": ["linkedin", "devto"],
        "description": "High-authority LinkedIn technical post + in-depth Dev.to article before US engineering standups."
    },
    # Window 3: Silicon Valley Morning / Global Tech Peak Prime
    "W3_VISUAL_PRIME": {
        "utc_start": 14,  # 14:00 UTC = 19:30 PM IST = 10:00 AM EST
        "utc_end": 16,    # 16:00 UTC = 21:30 PM IST = 12:00 PM EST
        "ist_display": "19:30 - 21:30 IST",
        "est_display": "10:00 - 12:00 EST",
        "name": "Visual Curriculum Prime (Shorts + Carousels)",
        "primary_actions": ["youtube", "instagram", "pinterest"],
        "description": "YouTube Short #1 + Instagram Enriched Carousel + Pinterest Pin during peak global dwell time."
    },
    # Window 4: US Afternoon Break / Tech Discourse
    "W4_TECH_DEBATE": {
        "utc_start": 17,  # 17:30 UTC (17) = 23:00 PM IST = 13:30 PM EST
        "utc_end": 20,    # 20:00 UTC = 01:30 AM IST = 16:00 PM EST
        "ist_display": "23:00 - 01:30 IST",
        "est_display": "13:30 - 16:00 EST",
        "name": "Tech Debate & Viral Commentary",
        "primary_actions": ["repost", "threads", "reply"],
        "description": "𝕏 Quote-Tweet with spicy engineering masala, Threads discussion, and sniper replies."
    },
    # Window 5: US Evening Relaxation & Mobile Feed Scroll
    "W5_EVENING_VIDEO": {
        "utc_start": 22,  # 22:00 UTC = 03:30 AM IST = 18:00 PM EST
        "utc_end": 24,    # 00:00 UTC = 05:30 AM IST = 20:00 PM EST
        "ist_display": "03:30 - 05:30 IST",
        "est_display": "18:00 - 20:00 EST",
        "name": "Prime Evening Video & Visual Pin",
        "primary_actions": ["youtube_reel", "pinterest", "reply"],
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
    "linkedin_posts": int(os.getenv("MAX_DAILY_LINKEDIN", "1")),          # 1/business day (strict anti-cannibalization)
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
