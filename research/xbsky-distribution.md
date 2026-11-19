# X + Bluesky Distribution — Ranked Levers, Kill Criteria, Red Team

*Role: distribution strategist + red team for 𝕏 and Bluesky. Read-only analysis — no production code was modified.*
*Date: 2026-11-20.*
*Evidence base: `trial_metrics.json` (500 recent events, 2026-11-14 21:48 → 2026-11-19 20:01 UTC; lifetime summary since 2026-10-21), `post_history.json`, `config.py`, `.github/workflows/x_automater.yml`, `src/scheduler.py`, `src/web/app.py`, `scripts/x_follower_snapshot.py`, `data/growth_baseline.json`, and the existing swarm findings in `research/skeptic-findings.md` and `research/growth-strategy-findings.md`.*

---

## 0. Read this before any tactic is funded

**There is no outcome data on X or Bluesky. None.** The 500 recent events in `trial_metrics.json` carry exactly these fields: `action_type, content_preview, duration_s, is_dry_run, reason, status, target, timestamp`. There is no like, repost, reply-received, quote, impression, view, profile-visit, or follower field. The system counts what it *did*, never what it *caused*.

The dashboard is not a substitute: `/api/stats` sets `current_followers = 20  # Live follower base` as a literal constant (`src/web/app.py:258`) and computes `estimated_impressions = total_actions * 4500` (`src/web/app.py:270`). Its own `metric_transparency` block labels X followers `source: hardcoded_constant, status: simulated, is_estimated: true` and X impressions `source: cycles_x_4500, status: estimated` (`src/web/app.py:316-320`). `AUDIT_REPORT.md:24` says the same plainly, and `data/growth_baseline.json:3` states "No platform analytics API is connected, so reach, impressions, engagement rate, watch time, and demographics are NOT captured."

Consequences, applied literally for the rest of this document:

1. Every "success" below means *the platform accepted the API/browser action*, not that anyone engaged. `status: success` is a delivery receipt, not a growth result.
2. No lever may be called "working" on the strength of `trial_metrics.json`, `/api/stats`, `data/growth_baseline.json`, or any counter derived from cycles. Those are **activity logs**, and reporting them as wins is the vanity-metric failure mode this red team exists to kill.
3. The one honest verdict available for any tactic today is **"not yet measurable,"** never "working."
4. `data/x_followers.json` is **absent from the working tree**. The workflow has a best-effort snapshot step (`.github/workflows/x_automater.yml:164-167`) that the script itself describes as non-fatal because "X exposes no free public follower API" (`scripts/x_follower_snapshot.py:1-5`); on failure it writes `{followers: null, note: ...}` (`:74-86`). A `continue-on-error` snapshot with no file is theater, not measurement — consistent with `research/growth-strategy-findings.md:69-75,132`.

---

## 1. Distribution diagnosis (what is actually broken)

### 1.1 X originals: the infra failure is fixed, but the cap behavior is not yet characterized under the new limit

Recent window, by action (`trial_metrics.json:recent_events`):

| Channel | Events | success | failed | skipped | Honest read |
|---|---|---|---|---|---|
| X original post | 176 | 23 (13%) | 79 | 74 | 74 of the 79 failures are one error: `BrowserType.launch: Executable doesn't exist ... chromium_headless_shell-1255` |
| X reply | 39 | **0** | 3 | 36 | 35× "No high-engagement unreplied trending tweet found" (`:2469,2519,...`), 3× "submission timed out; retry blocked", 1× already reserved |
| X quote-tweet | 12 | **0** | 2 | 10 | 10× "No high-engagement unquoted trending tweet found", 2× timeout |
| Bluesky post | 130 | 101 (78%) | 1 | 28 | The only healthy publisher |
| Bluesky reply | 1 | 0 | 0 | 1 | Skipped: "Total daily limit reached (25/20)" — the only Bluesky-reply event ever |

Playwright failures are dated **11-14 through 11-17 only** (2/27/25/20 per day), then drop to **zero on 11-18 and 11-19** — post-fix, original-post success was 8 on each of those two days. This corroborates the manager's "browser missing, fixed in cloud" and means the historical ~46% failure rate is **stale for forecasting**. The workflow now installs Chromium unconditionally (`.github/workflows/x_automater.yml:60-63`), which is the correct fix.

But the skip pattern is a separate defect: 70 of the 74 skips cite `Daily original posts limit reached (8/6)` (37×) or `(8/8)` (33×); the other 4 are 7/6, 6/6 and a total-cap skip. The enforced cap in this data was **6–8/day, not 4**. Current config sets `MAX_DAILY_X_ORIGINALS = 4` (`config.py:136`) and the workflow exports `MAX_DAILY_X_ORIGINALS: '4'` / `MAX_DAILY_BLUESKY: '4'` (`.github/workflows/x_automater.yml:91-95`). The 4/4 caps are therefore **newer than this dataset**; the 14-day window must start from a fresh baseline, not from these counts.

### 1.2 The reply engine is a no-op, and its content would be off-niche even if it worked

`_pick_trending_target` samples 6 `GROWTH_ACCOUNTS` + 2 `VIRAL_ACCOUNTS` at random (`src/scheduler.py:832-838`). That viral list includes cinema, gossip, politics, finance and celebrity accounts — `taran_adarsh`, `filmfare`, `ANI`, `NDTV`, `narendramodi`, `unusual_whales`, `zerohedge`, `elonmusk`, `naval` (`src/scheduler.py:97-132`) — directly against the charter's niche constraint (`agents/README-X-BLUESKY.md:13-14`). The generated replies that did get reserved are not engineer-to-engineer takes: *"Imagine getting a CS degree just to have your entire overnight patch dictated by an unhinged reply guy with an anime PFP"* (`post_history.json:795`), *"Bro's really doing market research on okra while taking 55 minutes to deliver a cold khichdi. #Swiggy"* (`:806`), *"Bro literally just automated my inability to pick what to watch on Netflix for 45 minutes"* (`:817`). Eight such reservations are stuck at `status: unknown` with "retry blocked to prevent duplicates" — correct safety behavior, no reconciliation.

So there are **two independent blockers**: target discovery returns nothing (0/39), and the content that would be published is off-niche gossip/roast copy. Fixing only the scraper would turn a no-op into a reputation liability.

### 1.3 Bluesky is the only working channel, and it has never replied

Bluesky posts succeeded 101/130; the single failure was a network read timeout. The reply path is implemented and on-niche (`src/scheduler.py:2457-2509`, search queries `"AI benchmark OR LLM"`, `"inference latency"`, `"open source model"`), and it would record `bluesky_replied_uris` (`:2496-2499`). **That key does not exist in `post_history.json`** — not a single Bluesky reply has ever completed. Its only recorded attempt was killed by the shared `MAX_DAILY_TOTAL` cap (25/20). This is the same starvation pattern the manager described for LinkedIn engagement being moved into its own concurrency group (`.github/workflows/x_automater.yml:28-30`): the posting job consumes the shared budget before the engagement step runs.

Bluesky is also the only platform where real per-post engagement is obtainable for free from the public AppView (`app.bsky.feed.getPostThread` returns `likeCount/repostCount/replyCount/quoteCount`). The current live-metrics function fetches **only profile-level** `followersCount/followsCount/postsCount` (`src/web/app.py:148-202`). Free measurement exists and is not being collected.

### 1.4 First-hour interaction, profile, timing, follows, cross-posting: status

- **Profile**: staged copy exists in `config.py:36-54` (`CREATOR_NAME`, `CREATOR_BIO`, narrow niche, no outbound link), but `src/web/app.py:258` still reports a hardcoded follower count and `data/growth_baseline.json` has no conversion data. We cannot confirm the copy is live on either platform, nor its effect.
- **First-hour interaction on our own posts**: capability exists only for LinkedIn (`src/linkedin_automater.py:808`), not for X or Bluesky. There is no X/Bluesky "reply to a comment on our post" path.
- **Timing**: `ALGORITHMIC_WINDOWS` defines five IST slots (`config.py:75-126`) but cadence is a 6-hour cron (`.github/workflows/x_automater.yml:4-6`), so slot assignment is incidental. With a follower base reported as 20 (and no real follower count), timing effects are unmeasurable noise.
- **Cross-posting / dedupe**: `posted_tweet_hashes` has 236 entries, yet near-duplicate topics are recorded as separate posts (twice 20 minutes apart with identical hash per `research/growth-strategy-findings.md:79`), and `posted_bluesky_topics` has only 2 recorded topics — topic-key coverage across Bluesky is effectively absent.
- **Visual suppression**: charter bans outbound links in bodies (`agents/README-X-BLUESKY.md:10-11`; `config.py:43` `ALLOW_LINKS_IN_POSTS=false`). There is no attachment-level outcome data anywhere, so "visuals help/hurt" is unfalsifiable here; the generator is documented as producing invented metric bars (`research/skeptic-findings.md:32,82-84`).

---

## 2. Ranked non-content levers — 𝕏

ROI × ease, 1–5 each. Ease assumes no new product surface unless noted. **"Small-account failure" is the attack on my own recommendation**: the specific reason this lever may produce nothing at ~20 followers / no measurable reach.

| # | Lever | ROI | Ease | Score | Why it might not work on a small account |
|---|---|---|---|---|---|
| 0 | **Prerequisite: prove X originals are live at cap 4** | — | — | gate | Post-fix success was 16/16 across 2 days but those days include 73 cap skips under the *old* 6/8 cap. If 4/day is not actually enforced, every lever below is measured against a moving baseline. No growth credit until ≥80% delivery at the new cap for 7 days. |
| 1 | **Profile/bio conversion** | 5 | 5 | **25** | Copy is already staged (`config.py:36-54`); work is verification only. Small-account failure: a perfectly optimized bio converts zero people if nobody visits the profile — and we cannot count visits. Treat as cheap hygiene, never as a measured win. |
| 2 | **Dedupe + queue reconciliation** | 4 | 5 | **20** | Normalize topic keys, drain 8 stuck `pending_x_actions` (`post_history.json`). Small-account failure: this stops spam signals and wasted capacity; it creates no demand. It is a guardrail, not growth. |
| 3 | **Reply-target redesign** (on-niche small/mid accounts; only after scraper + content fixes) | 5 | 2 | **10** | Highest theoretical ROI, lowest current readiness: 0/39, random sampling from an off-niche viral list (`scheduler.py:97-132,832-838`). Small-account failure: a small account's reply to a mega-account is buried in seconds; even a perfect reply may earn zero impressions. Requires a real log before scaling. |
| 4 | **First-hour interaction on our own posts** | 4 | 2 | **8** | No X capability exists. Small-account failure: at ~20 followers there may be *zero* inbound comments to answer; building the capability could be pure cost. Only worth it if the outcome log shows ≥1 substantive inbound comment per post. |
| 5 | **Visual suppression / no-link discipline** | 2 | 4 | **8** | Keep links out of bodies (already enforced, `config.py:43`); do not add decorative/invented visuals. Small-account failure: reach suppression is unmeasurable here; this is "avoid harm," not a growth tactic. |
| 6 | **Quote posts** | 3 | 2 | **6** | 0/12, same target-selection defect (`scheduler.py:1027`). Small-account failure: a quote from a low-authority account rarely travels, and attaching a take to a viral thread is the pile-on risk in §6. Keep at 0 until #3 is proven. |
| 7 | **Follows** | 2 | 2 | **4** | Small-account failure: following does not cause reciprocal follows; the current lists are brands/celebrities (`linkedin_network.json` pattern) who never follow back. Count of follows is a vanity metric. |
| 8 | **Timing** | 2 | 2 | **4** | Small-account failure: with no audience online and no impression data, slot optimization is indistinguishable from random. Defer until #0 and the outcome log exist. |
| 9 | **Cross-posting the same text to X and Bluesky** | 1 | 3 | **3** | Small-account failure: identical posts on both platforms advertise automation to two audiences at once; it wastes generation budget (`.github/workflows/x_automater.yml:91-93`) and cannot be attributed. Do not use as a growth lever. |

**X order:** verify delivery (gate) → profile + dedupe (cheap hygiene) → reply-target redesign (the only real growth engine, gated on measurement) → first-hour capability (conditional) → quote posts / follows / timing / cross-post (deferred or vetoed).

---

## 3. Ranked non-content levers — Bluesky

| # | Lever | ROI | Ease | Score | Why it might not work on a small account |
|---|---|---|---|---|---|
| 1 | **Profile/bio conversion** | 5 | 5 | **25** | Same staged copy (`config.py:36-54`), verify it is live on the Bluesky profile. Small-account failure: no profile-visit or follow-conversion data today; may convert nobody. Cheap, but not a demonstrable win. |
| 2 | **Turn on the Bluesky reply loop** | 5 | 4 | **20** | Code is ready and on-niche (`scheduler.py:2457-2509`); the sole recorded attempt was killed by `MAX_DAILY_TOTAL` (25/20). Give it a dedicated cap/concurrency lane, as was done for LinkedIn engagement (`.github/workflows/x_automater.yml:28-30`). Small-account failure: on a small federated account, a reply only travels if it is early and substantive; the generated reply quality is unproven and there is no reply-level log. This is the highest-upside **measurable** lever because AT Protocol exposes per-post counts. |
| 3 | **Real outcome instrumentation via public AppView** | 5 | 3 | **15** | `app.bsky.feed.getPostThread` yields like/repost/reply/quote counts; today only profile counts are fetched (`src/web/app.py:148-202`). Small-account failure: with 101 posts in 5 days but few followers, counts may be near-zero and noisy — that is a reason to log, not to declare failure. No tactic is evaluated before this exists. |
| 4 | **Dedupe / topic coverage** | 4 | 5 | **20** | `posted_bluesky_topics` has 2 entries; extend topic-key logging. Small-account failure: prevents repetition that reads as bot behavior; creates no engagement by itself. |
| 5 | **Follows (targeted AI-engineering practitioners)** | 3 | 2 | **6** | `scripts/bluesky_follow.py` exists. Small-account failure: on Bluesky, follows shape *your own feed* more than your reach; no evidence anyone follows back. Do not report follow count as growth. |
| 6 | **Timing** | 2 | 3 | **6** | Small-account failure: Bluesky's feed rewards reply/chat activity more than clock time; without impression data any slot change is untestable. |
| 7 | **Visual suppression** | 2 | 3 | **6** | No links in bodies; no decorative visuals with invented numbers. Small-account failure: zero attachment-level measurement, so only a guardrail, never a lever. |
| 8 | **Quote posts** | 2 | 2 | **4** | Smaller pile-on surface than X but same low-authority problem. Small-account failure: a quote with no audience behind it gets no distribution. Defer. |
| 9 | **Cross-posting X content verbatim** | 1 | 3 | **3** | See X #9. Small-account failure: looks automated, un-attributable. |

**Bluesky order:** verify profile → instrument AppView counts (prerequisite) → enable reply loop in its own budget lane → dedupe → targeted follows/timing (later, evidence-gated).

---

## 4. Minimum real log we need (blocking prerequisite)

Before any tactic is judged, capture one row per published post and one per reply, from real platform data, into a new append-only log (e.g. `data/xbsky_outcomes.jsonl`):

```
platform, post_uri_or_url, published_at_utc, action_type(original|reply|quote)
at_24h: {likes, reposts, replies, quotes, impressions_if_available}
at_48h: {same fields, profile_visits_if_available, follower_delta}
at_7d:  {same fields}
guardrails: {contains_unsourced_number: bool, on_niche: bool, has_link_in_body: bool}
for replies: target_handle, target_niche, reply_was_early(<60min), reply_received
source: "real_api" | "manual_platform_capture"   # never "estimated"
```

- **Bluesky**: populate counters from public AppView `getPostThread` / `getAuthorFeed` (fields `likeCount`, `repostCount`, `replyCount`, `quoteCount`). This is real, free, and available today (`src/web/app.py:148-202` currently fetches only profile counts).
- **X**: no free public engagement API. Accept **manual capture by the owner** at 24h/48h/7d for each post, or a best-effort logged-in scrape recorded with `source: manual_platform_capture`. If a value cannot be captured, write `null` — never a derived constant. Replace `data/x_followers.json` snapshots with real values only; keep `null` when the scrape fails (`scripts/x_follower_snapshot.py:74-86`).
- **Day 0 baseline**: capture trailing-20 published posts per platform *before* changing anything. Record it in `research/experiment-log.md` with hypothesis, single changed variable, primary metric, minimum effect worth keeping, and kill criteria **written before launch** (aligns with `research/skeptic-findings.md:98-100`). If a criterion is written after seeing the result, discard the result.

Nothing in §5 is readable until this log exists.

---

## 5. Fourteen-day metrics and kill criteria

Targets are deliberately small-account-realistic. "n" is the number of published posts in the arm; with 4/day caps, n should be ~14–28 per platform if delivery holds, but **if the log is missing, the metric is unread and sits in the kill column by default**.

| # | Metric | Source | 14-day target | Kill criterion — stop and revert if… |
|---|---|---|---|---|
| 1 | X original delivery rate at cap 4 | `trial_metrics.json` `status` | ≥80% success on attempts that are not cap-skips | <50% after the browser fix (baseline 23/176 = 13%) → infra blocker; no growth credit for X |
| 2 | Bluesky reply loop completion | `data/xbsky_outcomes.jsonl` + `bluesky_replied_uris` | ≥1 reply/day on ≥7 days, on-niche | Key still absent or 0 replies after 7 days → engagement step is starved again; revert to no engagement claims |
| 3 | Bluesky per-post engagement (median likes+reposts+replies at 48h) | AppView counters | ≥1 substantive interaction on ≥50% of posts (n≥14) | Median 0 across 14 posts → distribution is dead; stop adding volume and stop calling Bluesky "healthy" |
| 4 | X per-post engagement (median at 48h) | manual capture | ≥1 substantive interaction on ≥50% of posts (n≥14) | Median 0 across 14 posts → originals are publishing into a void; freeze scaling |
| 5 | Reply quality: share of replies on-niche with no invented number | log guardrails | 100% on-niche, 0 unsourced numbers | Any off-niche roast/gossip reply or unsourced number ships → kill replies immediately, regardless of engagement (see `post_history.json:795,806,817`) |
| 6 | X reply completion rate | `trial_metrics.json` | >20% before any reply work is funded | Baseline is 0/39 — already below kill. Do not allocate growth effort until #1 and #3 pass |
| 7 | Net real follower delta (X + Bluesky), 14d | `data/x_followers.json` real values + AppView `followersCount` | Net >0 | Net ≤0 after 14 days of full execution → activity produces no audience; freeze automation and escalate positioning |
| 8 | Duplicate posts / week (both platforms) | `post_history.json` normalized topic key | 0 | Any duplicate in 14 days → dedupe fix failed; hard-stop publishing until resolved |
| 9 | Stuck `pending_x_actions` count | `post_history.json` | 0 | Grows beyond 8 baseline → idempotency queue is leaking; stop reply/quote actions |
| 10 | Maintainer time | time log | ≤30 min/week | >30 min/week → kill; this is an automated account, not a second job |

**Guardrails on the experiment:** do not extend the window to "get more data." If a metric has no real source by Day 3, it stays in the kill column. Do not compare X to Bluesky or either to an "industry average"; within-account, same slot and pillar only. Never declare a win from a counter that is estimated or hardcoded (`src/web/app.py:258,270,316-320`).

---

## 6. Red team — how "engagement anyhow" fails here

| Failure mode | Mechanism in this repo | Verdict |
|---|---|---|
| **Off-niche virality** | `VIRAL_ACCOUNTS` mixes cinema, politics, finance and celebrity accounts (`scheduler.py:97-132`); generated replies are roasts (`post_history.json:795,806,817`); `config.py:23-28` still lists `wealth_finance, viral_culture, work_life_debates` as default niches | Never reply/quote for reach on these threads. Narrow the list; any off-niche reply is an automatic kill (#5) |
| **Reply spam / automation detection** | 4/day caps exist (`config.py:136-139`), but recent data shows 8/day X originals and 12/day Bluesky — a bot-shaped cadence. Near-duplicate topics and identical hashes already shipped (`research/growth-strategy-findings.md:79`) | Keep caps at 4/4; no sub-6h loops; no bulk replies. Dedupe before scaling |
| **Quote-tweet pile-on** | Quoting a viral thread attaches our handle to a fight we do not control; 0/12 success shows we have no expertise doing it safely (`scheduler.py:1027`) | Do not fund quote posts during the 14-day window |
| **Credibility loss via invented numbers** | The dashboard itself invents followers and impressions (`src/web/app.py:258,270`); the generator is primed to produce "realistic values with units" (`research/skeptic-findings.md:30,82-84`). Engineers check numbers | Any unsourced number is a trust breach, not a style issue. Aligned with the existing outright veto in `research/skeptic-findings.md:158-171` |
| **Measurement illusion** | 52%+ of events are skips; raising output against a broken reply engine and estimated dashboard manufactures "growth" that is only activity | Only real captured outcomes count. No win from cycles, attempts, or `/api/stats` |

### Veto outright

**I veto the "viral sniper reply/quote for reach" tactic as currently implemented** — randomly sampling `VIRAL_ACCOUNTS` (`scheduler.py:97-132,832-838`) and generating roast/gossip replies (`post_history.json:795,806,817`) on politics, celebrity, finance or cinema threads. It is not a cap-and-test item: it violates the niche and no-deception constraints (`agents/README-X-BLUESKY.md:3-5,13-14`), and on a small personal developer account the downside is irreversible credibility loss while the upside is a reply buried under thousands of others. Replacing the target list with on-niche AI-engineering accounts and requiring a substantive, sourced reply is a *different* tactic and may be tested after instrumentation; the current one dies now.

**Second veto (cheap to honor, fatal if ignored):** never report `/api/stats` values, `trial_metrics.json` counters, or X-follower snapshots with `followers: null` as evidence of engagement. They are hardcoded, estimated, or empty by construction.

---

## 7. One ordered 3-action plan

**Action 1 — Days 1–2: Build the truth layer (blocking).**
Add `data/xbsky_outcomes.jsonl`; pull Bluesky per-post counters from public AppView; set manual X capture at 24h/48h/7d; replace estimated/hardcoded dashboard inputs with real-or-null; capture Day-0 trailing-20 baselines and pre-register hypotheses/kill criteria in `research/experiment-log.md`. Verify the staged profile copy is live on both platforms and that X originals deliver at the new cap of 4. **Change no content and add no volume in these two days.** Exit: every §5 metric has a real source (first value may be zero) and X delivery ≥80%.

**Action 2 — Days 3–10: Turn on the only compounding engine.**
Enable the Bluesky reply loop in its own cap/concurrency lane so `MAX_DAILY_TOTAL` cannot starve it (`trial_metrics.json` last event: "Total daily limit reached (25/20)"; `.github/workflows/x_automater.yml:28-30` is the precedent for a dedicated lane). Require on-niche targets and substantive, source-safe replies — the off-niche sniper is vetoed (§6). Keep X replies/quote posts at zero; keep caps at 4/day. Exit: ≥1 on-niche reply/day on ≥7 of the days, 0 guardrail breaches (#5), and the `bluesky_replied_uris` key exists and grows.

**Action 3 — Days 8–14: Read the real log, then spend only on what passes.**
Apply §5 literally. If Bluesky reply posts show measurable interaction, continue at cap; if X originals deliver but engagement is 0, freeze X scaling and escalate positioning rather than adding volume. Normalize dedupe keys and drain the 8 stuck `pending_x_actions`. Only after cadence and measurement are stable, test one posting-time shift within a single slot — never quote posts, follows-count, or cross-posting as growth levers. On Day 14: keep what passed, stop what failed, and do not extend a dead experiment.

---

## Return to manager

- **Top 3 findings:** (1) X originals are probably fixed (Playwright errors end 11-17; 8/8 successes on 11-18 and 11-19) but the recent data predates the new 4/4 caps, so there is no clean baseline; (2) the X reply/quote loop is a true no-op — 0/39 replies with 35 "no suitable target" skips, 0/12 quotes — and its generated content is off-niche roast/gossip (`post_history.json:795,806,817`), so fixing the scraper alone would convert a no-op into a liability; (3) Bluesky is the only healthy publisher (101/130) and the only platform with free real per-post measurement (public AppView), yet it fetches only profile counts and has never completed a single reply — its one attempt was killed by the shared daily cap.
- **Strongest recommendation:** instrument first, then enable the Bluesky reply loop in its own budget lane. It is the only lever that is simultaneously high-ROI, code-ready, and *measurable with real data*; everything on X stays gated until delivery at cap 4 and a real outcome log exist. Profile verification and dedupe are free hygiene, not wins.
- **Biggest uncertainty:** whether any of this changes engagement at all. With no outcome data, a hardcoded follower base of 20, and /api/stats impressions literally `cycles × 4500`, we cannot distinguish a real effect from noise — and at this account size the mechanics of reach (reply placement, timing, follows) may simply not produce a detectable signal within 14 days. That is a reason to build the log and accept "inconclusive," not to lower the bar or declare victory.
