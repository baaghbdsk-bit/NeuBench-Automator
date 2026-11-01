# 💼 Setting Up LinkedIn Automation on NeuBench-Automator

This guide walks through cloning this repository and setting it up **exclusively or primarily for LinkedIn** (autonomous B2B posts, comment auto-replies, and viral thought-leadership comments on peer posts).

---

## ⚡ Option A: Run 24/7 in GitHub Cloud (Recommended — Free & No Laptop Needed)

Your friend does **not** need to keep their laptop running. GitHub Actions will run the automation every 45 minutes around the clock for free.

### Step 1: Fork or Clone the Repository
1. Click **Fork** on the top right of your GitHub repository:
   `https://github.com/baaghbdsk-bit/NeuBench-Automator`
   (Or clone and push to a new private repository).

### Step 2: Get a Free Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Click **Create API Key** (100% free tier available).

### Step 3: Get the LinkedIn Session Cookie (1-Minute Setup)
To allow GitHub Actions to comment, post, and reply to comments on LinkedIn:
1. Run locally once:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   python main.py login-linkedin
   ```
   This opens a browser, lets her log in once, and generates `linkedin_session/cookies.json`.
2. Encode `cookies.json` to base64:
   - On Windows PowerShell:
     ```powershell
     [Convert]::ToBase64String([IO.File]::ReadAllBytes("linkedin_session/cookies.json"))
     ```
   - On Mac/Linux:
     ```bash
     base64 -w 0 linkedin_session/cookies.json
     ```

### Step 4: Add GitHub Repository Secrets
In her GitHub repository, navigate to **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions** $\rightarrow$ Click **New repository secret**:

| Secret Name | Value | Purpose |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | `AIzaSy...` | Free AI generator for thought leadership & replies |
| `LINKEDIN_COOKIES_BASE64` | Base64 string of `cookies.json` | Enables browser posting & auto-replying in cloud |
| `LINKEDIN_ACCESS_TOKEN` *(Optional)* | Official LinkedIn OAuth token | Enables direct REST API publishing |
| `LINKEDIN_PERSON_URN` *(Optional)* | e.g. `urn:li:person:XXXXX` | Account URN for API publishing |

### Step 5: Enable the GitHub Action
1. Go to the **Actions** tab in GitHub.
2. Click **NeuBench-Automator 24/7 Cloud Autopilot** $\rightarrow$ Click **Enable workflow**.
3. Done! GitHub Actions will now automatically post 2–3 thought-leadership articles a day, reply to incoming comments every 45 minutes, and comment on viral peer posts.

---

## 💻 Option B: Run Locally on a Computer / Laptop

If she prefers running it directly on her own computer:

### 1. Clone & Install
```bash
git clone https://github.com/baaghbdsk-bit/NeuBench-Automator.git
cd NeuBench-Automator
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### 2. Configure `.env`
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
LINKEDIN_ENABLED=true
MAX_DAILY_LINKEDIN=3
MAX_DAILY_LINKEDIN_PEER_COMMENTS=0
```

### 3. Log In to LinkedIn Once
```bash
python main.py login-linkedin
```
A browser will pop up. Enter the LinkedIn login details and complete 2FA once. The session is saved locally in `linkedin_session/`.

### 4. Run or Schedule
- **Publish a LinkedIn post right now**:
  ```bash
  python main.py linkedin
  ```
- **Check and reply to comments on own posts**:
  ```bash
  python main.py linkedin-replies
  ```
- **Run the autonomous 24/7 daemon loop**:
  ```bash
  python main.py start
  ```
