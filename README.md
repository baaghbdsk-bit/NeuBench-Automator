# 🚀 X-Post-Automater

An automated, 100% free growth engine for X (Twitter) designed to maximize impressions, engagement, and reach toward Creator Monetization.

---

## ⚡ Quick Start

### 1. Verification & Status
Verify that your login session and Gemini API are active:
```powershell
.\venv\Scripts\python.exe -c "from src.twitter_client import TwitterClient; print('Logged in:', TwitterClient().is_logged_in())"
```

### 2. Test Content Generation (No browser opened)
Finds real-time trends and previews AI takes/polls/replies:
```powershell
.\venv\Scripts\python.exe main.py test
```

### 3. Post a Single Test Tweet (Live on your profile)
Pulls a trending topic, generates a polarizing hot take, and posts it to your account:
```powershell
.\venv\Scripts\python.exe main.py post
```

### 4. Sniper Reply to a Specific Viral Tweet
Reply under any viral tweet with an AI-crafted take:
```powershell
.\venv\Scripts\python.exe main.py reply --url "https://x.com/username/status/123456789"
```

### 5. Start the Autonomous 24/7 Engine
Runs in the background, alternates between sniper replies (~75%) and original debate tweets (~25%), spaced with human jitter intervals (35–75 mins):
```powershell
.\venv\Scripts\python.exe main.py start
```

---

## ⚙️ Configuration (`.env`)

You can customize your bot's behavior in `.env`:
* `POSTS_PER_DAY`: Target posts per day (default `18`)
* `REPLY_PERCENTAGE`: Percentage of sniper replies vs original tweets (default `75`%)
* `POST_INTERVAL_MIN_MINUTES`: Minimum sleep between posts (default `35`)
* `POST_INTERVAL_MAX_MINUTES`: Maximum sleep between posts (default `75`)
* `GEMINI_MODEL`: Primary LLM (`gemini-3.5-flash-lite` with automatic fallback to `gemini-3.8-flash`)

---

## 🛡️ Anti-Detection & Safety Rules
* Operates via **stealth Playwright browser session** with human-like typing delays (30ms–90ms per keystroke).
* No repetitive robotic patterns.
* No hashtag spam (prevents algorithmic suppression).
* Keeps full track of all posted URLs in `post_history.json` to never repeat content.

