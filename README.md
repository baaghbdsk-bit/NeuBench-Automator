# ⚡ Omnichannel Growth Suite



> **A creator-first posting engine for 𝕏, Bluesky and LinkedIn.**

> Publish, grow, and automate one consistent creator voice across **𝕏 (Twitter)**, **Bluesky**, and **LinkedIn** — **$0 paid API fees**, no product promotion, powered by Google Gemini.



---



## 🎯 What is this?



Most social media automation tools blindly blast the exact same message across every platform or demand $100–$500/month for enterprise API paywalls. 



This is an open, full-stack creator suite built for developer founders, indie hackers, and creators who want reach instead of brand noise:



1. **Native Omnichannel Matrix (3 Platforms):**

   * **𝕏 (Twitter):** Contrarian AI/engineering takes, benchmark debates, and replies under accounts your audience already follows.

   * **🦋 Bluesky:** Developer-focused, open-source weight analyses, and AT Protocol updates ($0 official XRPC REST API).

   * **💼 LinkedIn:** Executive B2B thought-leadership with structured hooks, bullet insights, and discussion prompts — capped at 1 post/day.

2. **Growth Engine, Not a Billboard:**

   * No brand names, no product pitch, no external links in post bodies (links suppress reach on X and LinkedIn).

   * Near-duplicate topic detection stops the same take from being recycled.

   * Engagement-first reply targeting on AI/engineering accounts.

3. **Sleek Web Command Center (`http://127.0.0.1:8000`):**

   * Fast, modern UI with Linear-inspired icon rail, dark/light theme, live milestone trackers, and topic routing matrix.

   * **1-Click "Broadcast All 3 Platforms"**: Generate and dispatch multi-platform takes with a single button.

   * **24/7 Autopilot Master Switch**: Enable or pause fully autonomous background posting right from the dashboard.

4. **$0/Month Architecture:**

   * Utilizes local persistent browser contexts (Playwright) to eliminate expensive 𝕏 and LinkedIn API subscriptions.

   * Official AT Protocol for Bluesky.

   * Google Gemini free tier for content generation.



---



## 📊 Platform Capability Matrix



| Platform | Target Audience | Algorithmic Driver | Max Length | Technology | Cost |

| :--- | :--- | :--- | :--- | :--- | :--- |

| **𝕏 (Twitter)** | Tech Founders, VCs, AI Devs | Bookmark & Reply velocity | 280 chars | Playwright (Session) | **$0** |

| **🦋 Bluesky** | Open-source devs, AT Protocol | Firehose syndication | 300 chars | Official XRPC API | **$0** |

| **💼 LinkedIn** | CTOs, VP Eng, Enterprise Leads | Dwell time & comments | 3,000 chars | Playwright (Session) | **$0** |





---



## 🚀 Quick Start Guide



### 1. Clone & Install Dependencies

```powershell

git clone https://github.com/baaghbdsk-bit/X-Post-Automater.git NeuBench-Automator

cd NeuBench-Automator



# Create and activate virtual environment

python -m venv venv

.\venv\Scripts\activate



# Install requirements & Playwright browsers

pip install -r requirements.txt

playwright install chromium

```

*(Windows users can simply double-click `setup.bat` to automate this step!)*



### 2. Configure Environment (`.env`)

Create a `.env` file from the example:

```env

# 1. Google Gemini AI Key (100% Free at aistudio.google.com)

GEMINI_API_KEY=your_gemini_api_key_here

GEMINI_MODEL=gemini-3.5-flash-lite



# 2. Automation Cadence & Quotas

POSTS_PER_DAY=4

POST_INTERVAL_MIN_MINUTES=350

POST_INTERVAL_MAX_MINUTES=370

MAX_DAILY_TOTAL=20

MAX_DAILY_ORIGINAL_POSTS=4

MAX_DAILY_REPLIES=12

# LinkedIn: 1 post/day. More than one suppresses reach.

MAX_DAILY_LINKEDIN=1

LINKEDIN_MIN_INTERVAL_MINUTES=720

DRY_RUN=false



# 3. Bluesky Credentials (Settings -> App Passwords)

BLUESKY_HANDLE=yourname.bsky.social

BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx



# 4. Target Niches (Comma-separated)

TARGET_NICHES=ai_tech,wealth_finance,viral_culture

```



### 3. Connect Your Social Accounts (One-Time Setup)

Sign in to each platform once so the automator can save your local encrypted session:

```powershell

# 1. Twitter / 𝕏

python main.py login



# 2. LinkedIn

python main.py login-linkedin









```

*(A browser window opens for each. Log in normally, see your feed, and press ENTER in the terminal. Your session is saved locally and never shared).*



### 4. Launch the Web Dashboard

```powershell

python main.py dashboard

```

Opens your command center at **`http://127.0.0.1:8000`**!



---



## ⚡ Running 24/7 Forever (Zero Daily Intervention)



Once your accounts are connected, you can run the automator 100% hands-free:



### Option A: Via Dashboard Toggle (Easiest)

1. Open the dashboard at `http://127.0.0.1:8000`.

2. Toggle the **"24/7 Autopilot Engine"** switch to **ACTIVE**.

3. The engine will automatically run in the background, curate trending topics, and post across all 3 platforms.



### Option B: Self-Healing Watchdog Supervisor (Terminal / Background)

The supervisor automatically restarts the engine if your PC temporarily loses Wi-Fi or encounters a network glitch:

```powershell

python scripts/watchdog_runner.py

```



### Option C: Windows Auto-Start on Boot (Permanent 24/7)

To have Windows automatically start the automator whenever your PC turns on:

1. Press `Win + R`, type `taskschd.msc`, and hit Enter.

2. Click **Create Basic Task** -> Name it `OmnichannelAutomator`.

3. Set Trigger: **"When the computer starts"** or **"When I log on"**.

4. Set Action: **"Start a program"**:

   * Program: `E:\X-Post-Automater\venv\Scripts\python.exe`

   * Arguments: `scripts/watchdog_runner.py`

   * Start in: `E:\X-Post-Automater\`

5. Check **"Run with highest privileges"** and save.



---



## ⌨️ CLI Command Cheat-Sheet



| Command | Action |

| :--- | :--- |

| `python main.py dashboard` | Launches the local Web UI at `http://127.0.0.1:8000` |

| `python main.py start` | Starts continuous 24/7 background autopilot loop |

| `python main.py omnichannel` | Immediately broadcasts 1 update across all 3 platforms |

| `python main.py post` | Generates and publishes an original hot take |

| `python main.py reply` | Finds a trending tweet from top AI leaders and posts a sniper reply |

| `python main.py repost` | Quote-tweets a viral take with contrarian perspective |

| `python main.py bluesky` | Generates and posts a take to Bluesky via AT Protocol |

| `python main.py linkedin` | Generates and publishes an executive post to LinkedIn |



| `python main.py metrics` | Displays verifiable 24-48h activity stats & rate limits |



---



## 🔒 Security & Privacy Notice



* **Local Session Privacy:** All session databases (`browser_session/`, `linkedin_session/`) and `.env` are strictly `.gitignored`.

* **Zero Credential Sharing:** Cookies remain 100% on your local machine and are never transmitted to any third-party server.

* **Organic Anti-Bot Guards:** Human-like typing jitter (30–80ms per character), randomized sleep pauses, and decoupled execution prevent account flagging.



---



## 🤝 Community & Support



* **Web App:** local dashboard (`python main.py web`)

* **𝕏 / Twitter:** [@GWorld34864](https://x.com/GWorld34864)


* **Bluesky:** [@creator](https://bsky.app/profile/creator.bsky.social)

* **GitHub:** [baaghbdsk-bit](https://github.com/baaghbdsk-bit)

