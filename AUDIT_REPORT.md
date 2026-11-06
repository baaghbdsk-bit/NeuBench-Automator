# X Automation Dashboard — Audit Report

## 1. Existing Dashboard Architecture
- **Primary dashboard**: FastAPI app in `src/web/app.py` (port 8000), Jinja2 template `src/web/templates/dashboard.html`. Run via `run_dashboard.bat` (calls `python main.py dashboard` — note: not a valid argparse action in `main.py`; mismatch).
- **Secondary (separate)**: `cloudflare_dashboard/` — static PWA "Omnichannel Growth" command center (Cloudflare Pages, D1 schema defined but unused).
- **Backend services**: `AutomaterEngine` (scheduler), `ActivityTracker`, `SafetyEngine`, `AIGenerator`, `TwitterClient`, platform clients (Bluesky, LinkedIn, Reddit, Threads).
- **State**: `post_history.json` (x_state), `linkedin_state`, `trial_metrics.json` (tracker), `topic_routing.json`, `.env`.
- **Automation**: Playwright browser sessions; Gemini AI; NeuBench API; trend sources (HN, Google Trends RSS, TechCrunch/BBC RSS, HuggingFace papers).

## 2. Existing Navigation & Features
Single-page dashboard with icon rail platform switcher: Omnichannel Hub, 𝕏 Suite, Bluesky, LinkedIn B2B Studio, Reddit AI Communities, Threads Discussion Studio. Plus NeuBench feed/radar, draft editors, publish buttons, settings, topic routing matrix, activity feed, safety caps, auth status, autopilot toggle, cloud deploy, ecosystem cross-promo.

## 3. Fully Working Functionality
- Multi-platform custom publishing (X, Bluesky, LinkedIn, Reddit, Threads) via Playwright + Gemini.
- Autopilot start/stop + status detection.
- Auth launchers (login scripts) + per-platform login state checks.
- NeuBench feed + multi-platform draft generation.
- Topic routing persistence.
- Idempotency/reservation system (`x_state`, `platform_state`) preventing duplicate publishes.
- Safety caps + dry-run mode.
- Live Bluesky metrics; Threads follower scrape.

## 4. Partially Working Functionality
- `/api/stats`: X followers hardcoded (20), impressions estimated (cycles×4500); LinkedIn/Reddit/Threads stats constants or derived.
- Reddit metrics cache never fetches live data.
- Cloudflare dashboard numbers entirely static; D1 schema unwired.
- Trend discovery exists in backend (`trend_hunter.py`) but not surfaced in dashboard UI.
- Engagement/reply opportunity discovery not exposed in UI.

## 5. UI-Only / Backend-Missing
- Cloudflare `stats.js` returns hardcoded constants (not D1).
- Cloudflare dashboard HTML hero numbers (384/79) hardcoded.
- No trend intelligence, influencer network, engagement opportunities, approval center, or analytics pages in main dashboard.
- `main.py dashboard` command referenced but absent.

## 6. Missing Functionality (vs new vision)
- Trend intelligence UI (Indian news, viral posts, political/cultural/tech debates).
- Indian influencer network DB, categorization, monitoring, prioritization.
- Engagement opportunity discovery, suggested replies, approval workflow, duplicate prevention, engagement history.
- AI reply assistant (contextual analysis, fact verification, multiple suggestions, quality eval, sensitive-topic detection, approval recommendations).
- Content calendar, draft management, approval center, thread creation UI.
- Real analytics (impressions, engagement rate, replies/reposts/likes, profile visits, follower growth, per-topic performance, reply-initiated conversation performance).
- Overview dashboard aggregating the above.

## 7. Redundant / Duplicate
- Two dashboards (FastAPI + Cloudflare) with overlapping but divergent metrics; recommend consolidating into FastAPI dashboard, keep Cloudflare as deploy target only.
- Omnichannel hub duplicates platform panes; can be consolidated.

## 8. Technical Limitations
- X API not used (browser automation only) → analytics limited to scraped/estimated values; API restrictions apply.
- No persistent DB for influencer/engagement data (JSON files only).
- Simulated metrics must be clearly labeled.
- `run_dashboard.bat` broken launch command.

## 9. Recommended Navigation Structure (reuse existing)
Overview | Trend Intelligence | Indian Influencer Network | Engagement Opportunities | AI Reply Assistant | Content Studio | Content Calendar | Publishing Queue | Approval Center | Engagement Analytics | Account Growth Analytics | Automation Controls | Execution Logs | Settings.
Reuse existing platform panes + publish endpoints + settings + safety panels; add new sections incrementally.

## 10. Recommended UI Improvements
- Consolidate two dashboards; fix `run_dashboard.bat`.
- Label simulated/estimated metrics clearly; add data freshness timestamps.
- Add empty states, error handling, loading indicators.
- Mobile responsiveness audit of icon rail.
- Prioritize actionable info (pending approvals, opportunities) over vanity charts.

## 11. Backend Changes Required
- Persist trend/influencer/engagement data (SQLite or D1) with schemas.
- Expose trend hunter results via API.
- Engagement opportunity pipeline + reply generation + approval state machine.
- Real analytics collection (where X API/Playwright permits) with provenance flags.
- Audit logging for failed requests and duplicate prevention.

## 12. Database Changes Required
- Tables: influencers, influencer_posts, trends, engagement_opportunities, reply_suggestions, approvals, published_replies, analytics_snapshots, execution_log. Reuse D1 schema style; or local SQLite for dev.

## 13. Prioritized Roadmap
1. Fix launch command + label simulated metrics.
2. Expose existing trend hunter + engagement backend via API (no new UI yet).
3. Add Overview dashboard aggregating existing data.
4. Content Studio (reuse draft editors) + Approval Center.
5. Engagement Opportunities + AI Reply Assistant.
6. Indian Influencer Network.
7. Analytics (real + clearly-labeled estimated).
8. Consolidate Cloudflare dashboard.

Awaiting approval before any code changes.
