# ⚡ NeuBench X-Post-Automater

> **The Official NeuBench Autonomous AI News & Creator Growth Engine for X (Twitter).**  
> Built for creators, founders, and builders who want to reach the **5 Million Verified Impressions** and **500 Followers** threshold for X Creator Ads Revenue Sharing without paying $100+/month for official API keys. Direct live integration with **[NeuBench](https://neubench.vercel.app/)**.

---

## 🎯 Who Is This For?

* **Indie Hackers & Tech Founders:** Build organic distribution and get eyes on your products while you focus on writing code.
* **AI Enthusiasts & Researchers:** Automatically track and debate frontier model drops, benchmarks, and breakthrough papers with our built-in **[NeuBench](https://neubench.vercel.app/)** integration.
* **Content Creators & Ghostwriters:** Automate high-velocity sniper replies under viral tweets to capture 50k–200k+ impressions daily.
* **High-Engagement Cultural Commentators:** Specially calibrated to dominate **Indian Tech & Cultural debates** alongside global heavyweights (`@IndianTechGuide`, `@peakbengaluru`, `@NDTV`, `@elonmusk`, `@sama`, `@kunalb11`).

---

## ✨ Core Features

* ⚡ **NeuBench Live AI Hub:** Seamlessly integrated with **[NeuBench](https://neubench.vercel.app/)**! Displays real-time breaking AI stories and a 266+ model benchmark leaderboard right on your dashboard, with 1-click **"Draft 𝕏 Tweet"** using Gemini.
* 🔍 **Multi-Stream Trend Hunter:** Pulls real-time spikes from Google Trends RSS (India & US), Hacker News Firebase REST API, NeuBench AI Radar, and TechCrunch/BBC World feeds for $0.
* 🤖 **Human-Voice AI Engine:** Powered by Google Gemini 3.5 Flash-Lite / 3.8 Flash. Strictly formatted: **zero spam hashtags**, authentic internet tone, cynical 1-liners, and debate hooks designed to spark replies.
* 🎯 **The Sniper Reply Strategy (60%):** Automatically snipes the latest posts from high-velocity accounts within minutes of publishing to land in the top comment section.
* 🔁 **Quote-Tweets with "Masala on Top" (20%):** Takes breaking news and quotes it with a polarizing counter-intuitive angle.
* 🚀 **Original Hot Takes & Polls (20%):** Generates high-dwell-time debate polls and questions to convert casual viewers into profile followers.
* 🛡️ **Safety & Warm-Up Engine:** Strict human-cadence cap (max 20 actions/day), random keystroke delays (30–80ms), and duplicate prevention to keep accounts safe from bot detection.
* 📊 **Gamified Monetization Dashboard:** High-density web UI (featuring a clean, high-contrast Light Mode default and 1-click Dark Mode toggle) tracking your live progress toward the 500 follower and 5M impression milestones.

---

## 🚀 Choose Your Setup Track

You can run **NeuBench X-Post-Automater** in two ways depending on your workflow:

| Feature | Track 1: Local Web Dashboard (Option B) | Track 2: 24/7 Cloud Actions (Option C) |
| :--- | :--- | :--- |
| **Best For** | Everyday laptop users, manual tweet curation | 24/7 autonomous growth without keeping PC on |
| **Runs When PC is Off?** | ❌ Only runs when computer is awake | ✅ **Yes, runs 24/7 in GitHub Cloud** |
| **IP Address** | Your home residential IP (safest from bot detection) | GitHub Actions cloud runner |
| **Cost** | **$0.00** | **$0.00** (Free 2,000 monthly runner minutes) |
| **Setup Time** | 2 minutes | 3 minutes |
| **Trade-offs / Cons** | Requires laptop to be open for scheduled cycles | IP changes per run; session cookie refresh needed every ~30-60 days |

---

## 💻 Track 1: Local Web Dashboard Setup (Option B)

### 1. Clone & Install
```powershell
git clone https://github.com/baaghbdsk-bit/X-Post-Automater.git
cd X-Post-Automater
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\playwright install chromium
```

### 2. Configure Environment (`.env`)
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_free_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
MAX_DAILY_TOTAL=20
MAX_DAILY_REPLIES=14
DRY_RUN=false
```
*(Get a free API key in 60 seconds at [aistudio.google.com](https://aistudio.google.com)).*

### 3. Log In to X (One-Time Setup)
Save your browser session securely on your machine:
```powershell
.\venv\Scripts\python.exe main.py login
```
*(A browser opens. Log into X normally, see your feed, and press ENTER in terminal).*

### 4. Launch the Dashboard
* **Option A (1-Click Windows):** Double-click `run_dashboard.bat` in the folder.
* **Option B (Terminal):**
  ```powershell
  .\venv\Scripts\python.exe main.py dashboard
  ```
Opens your local control center at **`http://127.0.0.1:8000`** with live milestone trackers, NeuBench AI Radar, trigger buttons, and real-time activity stream!

---

## ☁️ Track 2: 24/7 Free Cloud Setup (Option C - GitHub Actions)

Want the bot to post every 45 minutes around the clock even when your laptop is shut down?

1. **Fork or Duplicate Repository:**  
   Click **Fork** at the top right of this repository to copy it to your personal GitHub account. We recommend setting your fork to **Private** to protect your repository settings.
2. **Export Your Session Cookie:**  
   On your local machine after running `main.py login`, execute:
   ```powershell
   .\venv\Scripts\python.exe scripts\export_session_secret.py
   ```
   Copy the base64 string printed in your terminal.
3. **Add Encrypted Secrets to Your GitHub Repo:**  
   Go to your repository on GitHub:  
   **Settings ➔ Secrets and variables ➔ Actions ➔ New repository secret**:
   * Secret 1: `GEMINI_API_KEY` = *your Gemini API key*
   * Secret 2: `X_COOKIES_BASE64` = *paste the copied base64 string*
4. **Enable Workflow Permissions:**  
   In your repository: **Settings ➔ Actions ➔ General ➔ Workflow permissions**:  
   Select **"Read and write permissions"** and check **"Allow GitHub Actions to create and approve pull requests"**. *(This allows the cloud runner to save your daily cycle counts back to git without manual intervention).*
5. **Enable Workflows:**  
   Go to the **Actions** tab on GitHub and click **"I understand my workflows, go ahead and enable them"**.

*That's it! GitHub Actions will automatically wake up every ~45 minutes, check NeuBench and viral trends, craft authentic human commentary, publish to X, save progress, and go back to sleep — 100% free.*

---

### 🕹️ CLI Command Reference

* `python main.py dashboard` — Launch the local web dashboard.
* `python main.py run-once` — Execute a single cycle immediately.
* `python main.py post` — Publish 1 original hot take on current trending topic.
* `python main.py reply --url "https://x.com/.../status/..."` — Sniper reply under any tweet.
* `python main.py repost --url "https://x.com/.../status/..."` — Quote-tweet with commentary.
* `python main.py metrics` — View durable activity table and quota counts in terminal.
* `python main.py update-profile --name "Your Name" --bio "Your Bio"` — Update X profile via script.

---

## 🚀 Explore Our Ecosystem

Check out other high-performance AI tools built by our team:

* ⚡ **[NeuBench](https://neubench.vercel.app/):** Curated real-time AI news feed, LLM evaluations & 266+ frontier model benchmark leaderboard.
* 💬 **Connect with the Creator on X:** Follow [@GWorld34864](https://x.com/GWorld34864) (`vishnu rot`) for live creator growth, direct DMs, and feature requests.
* 🐙 **Developer Community:** Star and collaborate at [github.com/baaghbdsk-bit](https://github.com/baaghbdsk-bit).

---

## ⚖️ Ethical Automation & Safety

* **Account Health First:** We strictly limit operations to ~20 daily human-like actions to keep accounts in good standing.
* **No Unsolicited Mass DMs or Spam:** The bot only comments contextually on public trending threads.
* **Privacy:** Session tokens remain in your encrypted GitHub Secrets or local `.gitignored` folders and are never transmitted to third-party servers.
