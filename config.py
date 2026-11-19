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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

POSTS_PER_DAY = int(os.getenv("POSTS_PER_DAY", "4"))
REPLY_PERCENTAGE = int(os.getenv("REPLY_PERCENTAGE", "50"))
POST_INTERVAL_MIN_MINUTES = int(os.getenv("POST_INTERVAL_MIN_MINUTES", "350"))
POST_INTERVAL_MAX_MINUTES = int(os.getenv("POST_INTERVAL_MAX_MINUTES", "370"))

# Default high-traction niches for maximum engagement
TARGET_NICHES = [
    n.strip() for n in os.getenv(
        "TARGET_NICHES",
        "ai_tech,wealth_finance,viral_culture,work_life_debates"
    ).split(",") if n.strip()
]

# ==============================================================================
# CREATOR / GROWTH POSITIONING
# The accounts publish as a creator, not as a product brand. Keep links out of
# post bodies (external links suppress reach on X and LinkedIn) and keep the
# voice narrow enough to compound an audience.
# ==============================================================================
CREATOR_NAME = os.getenv("CREATOR_NAME", "Vishnu")
CREATOR_NICHE = os.getenv(
    "CREATOR_NICHE",
    "AI engineering, LLM benchmarks, developer tools and builder culture",
)
# External links in post bodies are disabled for reach. If a link is ever
# needed, it goes in the first comment on LinkedIn, never in the post body.
ALLOW_LINKS_IN_POSTS = os.getenv("ALLOW_LINKS_IN_POSTS", "false").lower() in ("true", "1")

# Public profile copy. Growth lives here: a clear niche, no product pitch, no
# outbound link in the bio that competes with the follow button.
CREATOR_BIO = os.getenv(
    "CREATOR_BIO",
    "AI engineering, LLM benchmarks and developer tooling. Building in public.",
)
CREATOR_HEADLINE = os.getenv(
    "CREATOR_HEADLINE",
    "AI engineering, LLM benchmarks & developer tooling | Building in public",
)
CREATOR_LOCATION = os.getenv("CREATOR_LOCATION", "Remote")

# Platform cadence (posts per day). LinkedIn is intentionally capped at 1/day:
# >1/day suppresses reach on professional feeds.
MAX_DAILY_LINKEDIN_POSTS = max(0, int(os.getenv("MAX_DAILY_LINKEDIN_POSTS", "1")))

# Omnichannel Expansion (X, Bluesky, LinkedIn)
BLUESKY_HANDLE = os.getenv("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.getenv("BLUESKY_APP_PASSWORD", "")
LINKEDIN_ENABLED = os.getenv("LINKEDIN_ENABLED", "true").lower() in ("true", "1")
LINKEDIN_ORGANIZATION_URN = os.getenv("LINKEDIN_ORGANIZATION_URN", "")
LINKEDIN_API_VERSION = os.getenv("LINKEDIN_API_VERSION", "202610")
LINKEDIN_MIN_INTERVAL_MINUTES = max(0, int(os.getenv("LINKEDIN_MIN_INTERVAL_MINUTES", "720")))
LINKEDIN_SCHEDULE_GRACE_MINUTES = max(0, int(os.getenv("LINKEDIN_SCHEDULE_GRACE_MINUTES", "60")))

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
        "primary_actions": ["post", "bluesky", "reply"],
        "description": "Morning kickoff with original posts, Bluesky takes, and viral replies."
    },
    # Slot 2: 1:00 PM IST (07:30 UTC) - Midday Engineering Masterclass
    "W2_MIDDAY_ENGINEERING": {
        "utc_start": 7,   # 07:00 - 08:30 UTC = 12:30 - 02:00 PM IST
        "utc_end": 9,
        "ist_display": "12:30 - 02:00 PM IST (Target 1:00 PM IST)",
        "est_display": "02:30 - 04:00 AM EST / 08:30 - 10:00 AM CET",
        "name": "Midday Engineering Masterclass & Benchmark Race",
        "primary_actions": ["bluesky", "reply", "linkedin"],
        "description": "Midday engineering masterclass across Bluesky, LinkedIn, and viral replies."
    },
    # Slot 3: 5:00 PM IST (11:30 UTC) - Evening Transition
    "W3_EVENING_TRANSITION": {
        "utc_start": 11,  # 11:00 - 12:30 UTC = 04:30 - 06:00 PM IST
        "utc_end": 13,
        "ist_display": "04:30 - 06:00 PM IST (Target 5:00 PM IST)",
        "est_display": "06:30 - 08:00 AM EST (US East Standup)",
        "name": "Evening Transition & Video Drop",
        "primary_actions": ["bluesky", "reply", "repost"],
        "description": "Evening transition with Bluesky takes, viral replies, and quote posts."
    },
    # Slot 4: 9:00 PM IST (15:30 UTC) - Prime US Midday & India Evening Peak
    "W4_PRIME_DISCOURSE": {
        "utc_start": 15,  # 15:00 - 16:30 UTC = 08:30 - 10:00 PM IST
        "utc_end": 17,
        "ist_display": "08:30 - 10:00 PM IST (Target 9:00 PM IST)",
        "est_display": "10:30 - 12:00 PM EST (US Peak Hours)",
        "name": "Peak US Prime Discourse & Technical Blueprint",
        "primary_actions": ["linkedin", "bluesky", "repost"],
        "description": "Peak US prime discourse with LinkedIn posts, Bluesky takes, and quote posts."
    },
    # Slot 5: 12:00 AM (Midnight) IST (18:30 UTC) - Silicon Valley Afternoon / Midnight Drop
    "W5_MIDNIGHT_SV_DROP": {
        "utc_start": 18,  # 18:00 - 19:30 UTC = 11:30 PM - 01:00 AM IST
        "utc_end": 20,
        "ist_display": "11:30 PM - 01:00 AM IST (Target 12:00 AM IST)",
        "est_display": "13:30 - 15:00 EST / 10:30 - 12:00 PST (SF Peak)",
        "name": "Silicon Valley Peak & Midnight AI Architecture Drop",
        "primary_actions": ["bluesky", "reply", "repost"],
        "description": "Silicon Valley peak and midnight drop with Bluesky takes, replies, and quote posts."
    }
}

# ==============================================================================
# ALGORITHMIC DAILY FREQUENCY CAPS (Guards against cannibalization & spam limits)
# ==============================================================================
CAPS_PER_PLATFORM = {
    "linkedin_posts": int(os.getenv("MAX_DAILY_LINKEDIN", str(MAX_DAILY_LINKEDIN_POSTS))),  # 1 post/day max
    "linkedin_peer_comments": int(os.getenv("MAX_DAILY_LINKEDIN_PEER_COMMENTS", "6")), # Max viral comments/replies per day (commenting on others' posts)
    # Accept both the current X-specific names and the legacy names used by
    # the workflow/README so the configured caps are actually enforced.
    "twitter_originals": int(os.getenv("MAX_DAILY_X_ORIGINALS", os.getenv("MAX_DAILY_ORIGINAL_POSTS", "4"))),
    "twitter_replies": int(os.getenv("MAX_DAILY_X_REPLIES", os.getenv("MAX_DAILY_REPLIES", "24"))),
    "twitter_reposts": int(os.getenv("MAX_DAILY_X_REPOSTS", os.getenv("MAX_DAILY_REPOSTS", "6"))),
    "bluesky_posts": int(os.getenv("MAX_DAILY_BLUESKY", "4")),            # One post every 6 hours
}

MAX_DAILY_LINKEDIN = CAPS_PER_PLATFORM["linkedin_posts"]


# Real-Time Push Alerts (Optional: Discord / Telegram)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
