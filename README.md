# ⚡ NeuBench X-Post Automator

> **The Official Omnichannel AI Social Growth Suite for [NeuBench](https://neubench.vercel.app/).**  
> Autonomous multi-platform distribution and creator growth engine powering **𝕏 (Twitter)**, **Bluesky**, **LinkedIn**, and **Threads** — zero paid API subscriptions, zero spam, powered by Google Gemini and NeuBench Live AI Radar.

---

## 🎯 What is NeuBench X-Post Automator?

Most social automation tools blindly spam the exact same text across every platform or charge $100+/month for locked-down enterprise APIs. **NeuBench X-Post Automator** changes the game:

1. **Intelligent Topic Routing Matrix:** Different topics belong on different platforms. Instead of blasting the same content everywhere:
   * **𝕏 (Twitter):** Contrarian hot takes, viral tech debates, Bengaluru work culture satire, and sniper replies under big accounts.
   * **🦋 Bluesky:** Open-source developer discussions, decentralized AT Protocol updates, deep model weights, and latency benchmarks.
   * **💼 LinkedIn:** Executive B2B thought-leadership (1-line hook + 3 high-value bullet insights + discussion prompt).
   * **🧵 Threads:** Casual behind-the-scenes building, relatable creator humor, and mobile community debate starters.
2. **Native NeuBench Integration:** Direct live feed with **[NeuBench](https://neubench.vercel.app/)** — pull breaking AI news and leaderboard stats across 266+ frontier models with 1-click omnichannel drafting.
3. **Narrow Left-Rail Command Center:** Linear / Slack-style icon rail (56px) allowing creators to switch instantly between the Omnichannel Hub, 𝕏 Suite, Bluesky XRPC Publisher, LinkedIn Studio, and Threads Studio.
4. **Zero Paid APIs ($0/month):**
   * **𝕏:** Residential browser session cookies via Playwright (bypassing $100–$5,000/mo API paywalls).
   * **Bluesky:** 100% free official AT Protocol XRPC REST endpoint (`https://bsky.social/xrpc/...`).
   * **AI Intelligence:** Google Gemini 3.5 Flash-Lite / 3.8 Flash free tier.

---

## ✨ Core Feature & Platform Matrix

| Platform | Target Audience | Algorithmic Multipliers | Best Topics | Format & Cost |
| :--- | :--- | :--- | :--- | :--- |
| **𝕏 (Twitter)** | Founders, VCs, Chronically Online Tech | Bookmark & Reply Velocity in first 15 mins | Hot Takes, Bengaluru Culture, AI Benchmarks | 280 chars • $0 Playwright |
| **🦋 Bluesky** | Open-source devs, researchers, AT Protocol | Custom Feeds & Firehose Syndication | Open weights, developer tooling, AT Protocol | 300 chars • $0 XRPC API |
| **💼 LinkedIn** | CTOs, VP Eng, B2B Founders, Tech Leads | Dwell time (>45s reads) & comment threads | Enterprise AI ROI, Team Architecture, Strategy | 3,000 chars • 1-Click Copy |
| **🧵 Threads** | Mobile creators, casual tech builders | High comment-to-like ratio, conversation trees | Relatable work life, creator questions, polls | 500 chars • 1-Click Copy |

---

## 🎛️ Interactive Topic Routing Matrix

You can customize exactly which topics route to which platform in the dashboard:

```
┌───────────────────────────────────────┬──────────┬───────────┬──────────┬─────────┐
│ Content Topic                         │ 𝕏        │ Bluesky   │ LinkedIn │ Threads │
├───────────────────────────────────────┼──────────┼───────────┼──────────┼─────────┤
│ 🧠 AI Models & Benchmarks (NeuBench)  │   ✅     │    ✅     │    ✅    │   --    │
│ 🔥 Contrarian Hot Takes & Debates     │   ✅     │    --     │    --    │   ✅    │
│ ☕ Work & Bengaluru Culture Satire    │   ✅     │    --     │    --    │   ✅    │
│ 🛠️ Open-Source & AT Protocol          │   --     │    ✅     │    --    │   --    │
│ 💼 B2B Thought Leadership & Strategy  │   --     │    --     │    ✅    │   --    │
│ 📈 Markets & Wealth Culture           │   ✅     │    --     │    ✅    │   --    │
│ 💬 Community Questions & Polls        │   ✅     │    --     │    --    │   ✅    │
└───────────────────────────────────────┴──────────┴───────────┴──────────┴─────────┘
```

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

## 🔒 Security & Risk Analysis

Security and account longevity are foundational to NeuBench X-Post Automator:

1. **Zero Credential Hardcoding:**
   * No API keys, passwords, or session tokens exist anywhere in the git history.
   * Credentials live exclusively in `.env` (locally gitignored) or encrypted GitHub Actions Secrets.
2. **Session Cookie Isolation:**
   * 𝕏 browser sessions are stored locally in `browser_session/` (strictly `.gitignored`).
   * For 24/7 Cloud Actions, the session cookie is encrypted via standard GitHub Secrets (`X_COOKIES_BASE64`).
3. **Anti-Bot & Anti-Shadowban Safeguards:**
   * **Strict Rate Limiting:** Hard human safety cap of ~20 total actions per day (replies, quotes, original posts).
   * **Organic Typing Emulation:** Keystrokes are typed character-by-character with 30–80ms random jitter rather than instant DOM value injection.
   * **Human Reading Pauses:** 2–5 second delays before submitting actions, mimicking human verification.
   * **Modal Dialog Scoping:** Uses modern `div[role="dialog"]` Playwright locators with `domcontentloaded` wait states to prevent hung browser tabs.
4. **Official Open Protocol Usage:**
   * Bluesky integration uses the official, publicly supported AT Protocol XRPC REST API (`com.atproto.server.createSession` and `com.atproto.repo.createRecord`), which has zero risk of account suspension when using an App Password.

---

## 🌐 Extending to Other Platforms

NeuBench X-Post Automator is designed with a pluggable adapter architecture:
* **Reddit (r/MachineLearning, r/LocalLLaMA):** Add an OAuth script in `src/reddit_client.py` using `praw` to automatically cross-post benchmark findings.
* **YouTube Community Posts:** Dispatch 1-click formatted community poll questions for creators with YouTube channels.
* **Telegram / Discord Webhooks:** Feed real-time NeuBench AI alerts into private community channels with 1 webhook URL.

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

### 4. Launch the NeuBench X-Post Automator Dashboard
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

## 🏷️ How to Rename Repository on GitHub

To rename your repo to `NeuBench-Automator` on GitHub:
1. Go to your repository on GitHub: `https://github.com/baaghbdsk-bit/X-Post-Automater`
2. Click **Settings** ➔ **General** (top tab).
3. Under **Repository name**, change `X-Post-Automater` to `NeuBench-Automator` and click **Rename**.
4. Update your local git remote:
   ```powershell
   git remote set-url origin https://github.com/baaghbdsk-bit/NeuBench-Automator.git
   ```

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
