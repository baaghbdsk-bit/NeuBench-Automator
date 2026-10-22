# ⚡ NeuBench-Automator

> **The Official Omnichannel AI Social Growth Suite for [NeuBench](https://neubench.vercel.app/).**  
> Autonomous multi-platform distribution and creator growth engine powering **𝕏 (Twitter)**, **Bluesky**, **LinkedIn**, and **Threads** — zero paid API subscriptions, zero spam, powered by Google Gemini and NeuBench Live AI Radar.

---

## 🎯 What is NeuBench-Automator?

Most social automation tools blindly spam the exact same text across every platform or charge $100+/month for locked-down enterprise APIs. **NeuBench-Automator** changes the game:

1. **Omnichannel Distribution with Voice Routing:** Different audiences require different voices. Gemini automatically shapes content per platform:
   * **𝕏 (Twitter):** Punchy, contrarian hot takes & high-velocity sniper replies under viral tech debates.
   * **🦋 Bluesky:** Technical, open-source builder takes formatted for the AT Protocol developer ecosystem (<300 chars).
   * **💼 LinkedIn:** Executive B2B thought-leadership (1-line hook + 3 high-value bullet insights + discussion prompt).
   * **🧵 Threads:** Mobile conversational starters designed to ignite organic comments and community dialogue.
2. **Native NeuBench Integration:** Direct live feed with **[NeuBench](https://neubench.vercel.app/)** — pull breaking AI news and leaderboard stats across 266+ frontier models with 1-click omnichannel drafting.
3. **Narrow Left-Rail Command Center:** Linear / Slack-style icon rail (~56px) allowing creators to switch instantly between the Omnichannel Hub, 𝕏 Suite, Bluesky XRPC Publisher, LinkedIn Studio, and Threads Studio.
4. **Zero Paid APIs ($0/month):**
   * **𝕏:** Residential browser session cookies via Playwright (bypassing $100–$5,000/mo API paywalls).
   * **Bluesky:** 100% free official AT Protocol XRPC REST endpoint (`https://bsky.social/xrpc/...`).
   * **AI Intelligence:** Google Gemini 3.5 Flash-Lite / 3.8 Flash free tier.

---

## ✨ Core Feature Matrix

| Feature | 𝕏 (Twitter) | 🦋 Bluesky | 💼 LinkedIn | 🧵 Threads |
| :--- | :--- | :--- | :--- | :--- |
| **Audience Focus** | Founders, investors, tech debates | Open-source devs, researchers | VP Eng, founders, tech leaders | Mobile community, casual creators |
| **Voice Style** | Contrarian, witty, cynical | Open, curious, engineering-first | Structured insight (Hook + 3 bullets) | Casual, conversational question |
| **Max Length** | 280 chars | 300 chars (AT Protocol standard) | 3,000 chars | 500 chars |
| **Publishing Method** | Headless Playwright / Cloud Action | Official AT Protocol XRPC REST API | 1-Click Copy / Webhook ready | 1-Click Copy / Mobile formatted |
| **Milestone Tracker** | 500 Followers & 5M Impressions | Open protocol reach & handle sync | B2B thought engagement | Community reply count |

---

## 🖥️ Modern Dashboard Architecture

* **Narrow Icon Rail (56px):**
  * `⚡` **Omnichannel Hub:** Multi-platform status overview and central NeuBench AI Radar.
  * `𝕏` **𝕏 Growth Suite:** Real-time follower (20/500) and impression (25k/5M) progress bars, daily caps, instant action triggers, and live bot stream.
  * `🦋` **Bluesky Studio:** AT Protocol connection status, live handle binding, 300-char meter, and direct XRPC dispatcher.
  * `💼` **LinkedIn Studio:** Structured B2B thought-leadership drafting pad and copy pipeline.
  * `🧵` **Threads Studio:** Mobile dialogue generator and engagement starter.
  * `☀️ / 🌙` **Theme Switcher:** Default crisp Light Mode with high-contrast Dark Mode toggle and Google Inter font rendering.
* **Omnichannel Draft Studio:** Click **"Draft Omnichannel"** on any story or benchmark in the NeuBench Radar to generate all 4 platform-tailored takes in parallel with a single click.

---

## 🚀 Quick Start Guide

### 1. Clone & Setup Virtual Environment
```powershell
git clone https://github.com/baaghbdsk-bit/X-Post-Automater.git NeuBench-Automator
cd NeuBench-Automator
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\playwright install chromium
```
*(Windows users can simply double-click `setup.bat` to automate this step!)*

### 2. Configure Environment (`.env`)
Copy `.env.example` to `.env`:
```env
# 1. Google Gemini API (Required - 100% Free)
GEMINI_API_KEY=your_free_gemini_key_here
GEMINI_MODEL=gemini-3.5-flash-lite

# 2. Automation Strategy
POSTS_PER_DAY=18
REPLY_PERCENTAGE=75
TARGET_NICHES=ai_tech,wealth_finance,viral_culture,work_life_debates
DRY_RUN=false

# 3. Omnichannel: Bluesky (AT Protocol - 100% Free)
BLUESKY_HANDLE=yourname.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# 4. Omnichannel: LinkedIn & Threads
LINKEDIN_ENABLED=true
THREADS_ENABLED=true
```
*(Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com). For Bluesky, create an App Password in Bluesky: Settings ➔ App Passwords).*

### 3. Log In to 𝕏 (One-Time Setup)
Save your browser session securely on your local device:
```powershell
.\venv\Scripts\python.exe main.py login
```
*(A browser opens. Log into X normally, see your feed, and press ENTER in the terminal).*

### 4. Launch the NeuBench-Automator Dashboard
* **Option A (1-Click Windows):** Double-click `run_dashboard.bat`.
* **Option B (Terminal):**
  ```powershell
  .\venv\Scripts\python.exe main.py dashboard
  ```
Opens your local command center at **`http://127.0.0.1:8000`** with live milestone trackers, NeuBench Radar, and platform studios!

---

## ☁️ 24/7 Cloud Engine (GitHub Actions)

Run autonomous cycles around the clock every ~45 minutes without leaving your computer on:

1. **Fork or Duplicate Repo:** Fork this repository to your personal GitHub account (recommend setting to **Private**).
2. **Export Session Cookies:**
   ```powershell
   .\venv\Scripts\python.exe scripts\export_session_secret.py
   ```
   Copy the base64 string printed in your terminal.
3. **Add GitHub Secrets:**  
   In your repository: **Settings ➔ Secrets and variables ➔ Actions ➔ New repository secret**:
   * `GEMINI_API_KEY`: *your Gemini API key*
   * `X_COOKIES_BASE64`: *paste the copied base64 string*
   * `BLUESKY_HANDLE` *(optional)*: *your Bluesky handle*
   * `BLUESKY_APP_PASSWORD` *(optional)*: *your Bluesky app password*
4. **Enable Workflow Permissions:**  
   **Settings ➔ Actions ➔ General ➔ Workflow permissions**: Select **"Read and write permissions"** and check **"Allow GitHub Actions to create and approve pull requests"**.
5. **Enable Workflows:**  
   Go to **Actions** tab on GitHub and click **"I understand my workflows, go ahead and enable them"**.

---

## 🕹️ CLI Command Reference

* `python main.py dashboard` — Launch the local omnichannel web dashboard.
* `python main.py run-once` — Execute an autonomous cycle immediately.
* `python main.py post` — Publish an original hot take on current trending topic.
* `python main.py reply --url "<tweet_url>"` — Sniper reply under any tweet.
* `python main.py repost --url "<tweet_url>"` — Quote-tweet with commentary.
* `python main.py metrics` — View durable activity table and quota counts in terminal.
* `python main.py update-profile --name "Your Name" --bio "Your Bio"` — Update X profile via script.

---

## 🌐 The NeuBench AI Ecosystem

* ⚡ **[NeuBench Web App](https://neubench.vercel.app/):** Real-time AI news feed, LLM evaluations & 266+ frontier model benchmarks.
* 💬 **Follow on 𝕏:** [@GWorld34864](https://x.com/GWorld34864) (`vishnu rot`) for live creator growth experiments, direct DMs & updates.
* 🐙 **Developer Community:** Star and build with us at [github.com/baaghbdsk-bit](https://github.com/baaghbdsk-bit).

---

## ⚖️ Safety & Ethical Automation Guidelines

* **Strict Human Limits:** Hard cap of ~20 total actions/day to keep accounts in pristine standing.
* **Random Jitter:** 30–80ms random keystroke delay emulation and organic human scrolling intervals.
* **Privacy:** All session cookies and credentials remain in your encrypted GitHub Secrets or local `.gitignored` folders.
