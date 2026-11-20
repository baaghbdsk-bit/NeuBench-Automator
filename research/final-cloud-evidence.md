# Final Validation — Live Cloud Evidence (LIVE CLOUD EVIDENCE angle)

**Evidence cut:** cloud-written state as present in `D:\x-linkdin-bluesky\NeuBench-Automator`, inspected 2026-11-20.
**Post-ship window analysed:** `2026-11-20T00:00:00Z` → `2026-11-20T09:03:25Z` (last cloud event in `trial_metrics.json:4,5013`).
**Source of truth:** only files written by the cloud workflow / code paths. No GitHub Actions logs, no credentials, no live browser, no platform analytics were available.

---

## Verdict: **FIX FIRST**

Two confirmed defects block a clean ship: (1) the X outcome log is **100% test-fixture data**, still being appended by local test runs into the production state path; (2) post-ship X and Bluesky **posting loops produced 0 successes in 32 attempts** — every attempt was rejected by the new evidence/voice gate. The LinkedIn side is healthy and its cadence fix is confirmed working, but a release whose measurement artifact is fake and whose two of three posting channels are stalled is not ready.

---

## 1. Quantified post-ship activity

`trial_metrics.json` holds 500 recent events (`tracker.py:187` caps at 500) spanning `2026-11-15T19:01:57Z` → `2026-11-20T09:03:25Z`. Exactly **64** events fall on 2026-11-20.

| Action type | Success | Skipped | Failed | Success rate |
|---|---:|---:|---:|---:|
| `original_post` (X) | 0 | 21 | 0 | 0% |
| `bluesky_post` | 0 | 11 | 0 | 0% |
| `linkedin_post` | 1 | 10 | 0 | 9.1% |
| `reply` (X) | 1 | 16 | 0 | 5.9% |
| `quote_tweet` (X) | 0 | 3 | 0 | 0% |
| `bluesky_reply` | 1 | 0 | 0 | 100% (n=1) |
| **Total** | **3** | **61** | **0** | **4.7%** |

### Dominant skip reasons (61 skips on 11-20)

| Category | Count | Share | Legitimate? |
|---|---:|---:|---|
| Evidence/voice gate (`unsourced number`, `weak voice`) | 33 | 54.1% | **Yes** — intended Wave 0 guardrail (`growth.py:360-391`, `SYNTHESIS.md:35-47`), but see BLOCKER 2 |
| LinkedIn cooldown / daily cap | 10 | 16.4% | **Yes** — cadence fix working (see NON-BLOCKER 1) |
| No high-engagement target found | 9 | 14.8% | Plausible discovery starvation; cannot verify without logs |
| X browser session not authenticated | 9 | 14.8% | **Suspicious** — see HYPOTHESIS 1 |

Top single reasons: `X browser session not authenticated; discovery skipped` (9), `No high-engagement unreplied trending tweet found` (6), `weak voice 6/10: {...}` (5), `LinkedIn daily cap reached (1/1)` (4), `No high-engagement unquoted trending tweet found` (3).

---

## 2. Are the reply loops producing successes?

**Marginally, and only for X and Bluesky — not LinkedIn.**

- **X replies: 1 success / 17 attempts.** `trial_metrics.json:4903-4910` — `2026-11-20T07:02:49Z`, target `https://x.com/karpathy/status/2116957135661945283`, duration 47.44 s. **Corroborated** by `post_history.json:533` (`replied_urls` contains that exact URL). This is a real published reply.
- **Bluesky replies: 1 success / 1 attempt.** `trial_metrics.json:4563-4570` — `02:24:16Z`, target `@pricepertoken.bsky.social`. **Not corroborated** anywhere else: `grep pricepertoken` matches only that one event, and `post_history.json:847+` `platform_history.bluesky.completed` records only `post:<hash>` entries, no replies. Single unverified event.
- **Quote-tweets: 0 / 3** — all skipped `No high-engagement unquoted trending tweet found` (`trial_metrics.json:4423-4430,4673-4680,4953-4960`).
- **LinkedIn peer engagement: 0 events.** `linkedin_engagement_history.json:1-4` is `{"version":2,"engagements":[]}`. No `linkedin_peer_comment`/`linkedin_reply` events exist in the 64 post-ship events.

Note: reply drafting is now gated too — `trial_metrics.json:5003-5010` shows a reply to `cursor_ai` skipped for `unsourced number: 9 second` (`scheduler.py:1701-1731`). Guardrail is working, but it further starves replies.

---

## 3. Are posting loops producing successes or only gate skips?

**X and Bluesky: only gate skips. LinkedIn: one real success.**

- `original_post`: 21/21 skipped. Every reason is `unsourced number: …` and/or `weak voice N/10: {…}` — e.g. `trial_metrics.json:4383-4390` (`unsourced number: 40%`), `:4443-4450` (`unsourced number: 4MB`), `:4693-4700` (`unsourced number: 10x`), `:4973-4980` (`weak voice 6/10`). **Zero** post-ship X originals published.
- `bluesky_post`: 11/11 skipped, same gate reasons — e.g. `:4403-4410` (`weak voice 4/10`), `:4593-4600`, `:4993-5000` (`weak voice 3/10`). **Zero** post-ship Bluesky posts published.
- `linkedin_post`: one success at `:4763-4770` (`06:02:19Z`, content "I spent a week debugging why our vector search latency spiked…"). The other 10 are legitimate cadence/cap skips.

**Interpretation:** the guardrails themselves are behaving correctly (they block unsourced numbers and weak openers exactly as specified). The failure is upstream: the generators are not producing drafts that can clear the gate under the new rubric. Per `growth.py:323-357`, the rubric requires voice ≥7/10 with POV ≥1 and specificity ≥1; the observed drafts score 3–6/10 with `stance: 0` in nearly every case. This is a generator/prompt problem, not a gate bug — but operationally, two of three posting channels are stalled.

---

## 4. Are outcome files being created with real records?

| File | Records | Assessment |
|---|---:|---|
| `data/linkedin_outcomes.json` | 1 | **REAL.** `data/linkedin_outcomes.json:5-16` — `posted_at 2026-11-20T06:02:19.289345Z`, `post_urn urn:li:ugcPost:7529423859377197057`, `visual_format notebook_carousel`, `measure_due_at 2026-11-22T06:02:19Z`. Cross-checks exactly against `linkedin_post_history.json:3,1206-1215` (`last_success_at`, same URN) and `trial_metrics.json:4763-4770`. All metrics `null` because the 48 h window is not due yet — **correct, not fabricated**. |
| `data/x_outcomes.json` | 30 (at last read; still growing) | **NOT REAL — test-fixture pollution.** See BLOCKER 1. All 30 `text` values are verbatim strings from `tests/test_x_trend_integration.py:34,66,76,89,100,125,138`; 0/30 have any non-null metric. |
| `data/bluesky_outcomes.json` | absent | File does not exist in `data/` although `x_automater.yml:156` commits it and `scheduler.py:1757-1778` writes it. No post-ship Bluesky post succeeded, so no new record was due; historical absence is unverified. |
| `linkedin_engagement_history.json` | 0 | Empty (`:1-4`). `SYNTHESIS.md:78` kill criterion is "still absent/empty after 7 days" — only ~1 day post-ship, so **not yet failed**, but zero evidence today. |
| `data/engagement_queue.json` | 0 | Stale: `last_updated 2026-11-06T16:02:56Z`, `opportunities: []`. Not a post-ship artifact. |
| `data/x_followers.json` | absent | Referenced by `x_automater.yml:149,156,178-179` but missing; no follower snapshot to verify. |

---

## 5. Cap / cooldown behaviour — any misbehaviour?

**LinkedIn caps behaved correctly (CONFIRMED):**

- Cooldown messages step monotonically: `419.2m → 478.1m → 538.8m → 601.7m → 657.9m → 718.4m`, all with `minimum interval: 720m` (`trial_metrics.json:4393-4400,4453-4460,4513-4520,4583-4590,4643-4650,4703-4710`). These are consistent with the last prior post at `2026-11-19T17:03:47Z` (`linkedin_post_history.json:1196-1204`) and with `config.py:67` (`LINKEDIN_MIN_INTERVAL_MINUTES=720`).
- First eligible post after 720 m published at `06:02:19Z` (`:4763-4770`).
- Immediately afterwards, every attempt was skipped with `LinkedIn daily cap reached (1/1)` (`:4823-4830,4883-4890,4923-4930,4983-4990`), matching `config.py:59,132` (`MAX_DAILY_LINKEDIN_POSTS=1`). **No over-posting; no false cap.**

**Minor pre-ship oddity (non-blocker):** `trial_metrics.json:4363-4380` — at `2026-11-19T23:14:57Z` two events say `Total daily limit reached (25/20).` The counter was 25 when it blocked at a cap of 20 (`safety.py:28,53-55`; workflow sets `MAX_DAILY_TOTAL: '20'` at `x_automater.yml:96`). This suggests the counter overshoots before gating, but it is outside the post-ship window and no such event occurs on 11-20.

**Suspicious, not confirmed:** X auth check — see HYPOTHESIS 1.

---

## 6. CONFIRMED issues

### BLOCKER B1 — `data/x_outcomes.json` is test-fixture data, and tests are still writing it into the production state path

- **Evidence (exact):** `data/x_outcomes.json` records use the literal strings from `tests/test_x_trend_integration.py` — `"Quantum Error Correction Threshold Achieved"` (`:34`), `"I cut context length last quarter and latency dropped. Most teams overfeed their models."` (`:76`), `"Cheap models vs frontier models"` / `"I switched to routing small requests and cost fell…"` (`:89,100`), `"ISRO Tests Cryogenic Upper Stage for Chandrayaan-4"` / `"I watched a cryogenic test fail…"` (`:125,138`). All 30/30 records match those fixtures; 0/30 have any metric.
- **Why it happens:** `_record_x_outcome()` writes to hard-coded `Path("data/x_outcomes.json")` (`src/scheduler.py:1733-1753`) and is called on every successful `_execute_original_post` (`src/scheduler.py:1521-1527`) **with no `dry_run` guard**. The tests set `self.engine.safety.dry_run = True` (`tests/test_x_trend_integration.py:25`) and patch `post_tweet` to return `True` (`:48,77,101,139`), so each test run appends fake "posts".
- **Live proof:** the file grew during this audit: 26 records at first read → 30 records at `09:57:51Z` (batches at `2026-11-20T09:36:46Z` and `09:57:51Z`, both fixture text); `LastWriteTime` advanced from 15:06 to 15:27 local (IST = UTC+5:30). There were **zero** successful `original_post` events on 11-20 in `trial_metrics.json`, so these records cannot be cloud posts.
- **Impact:** any claim that "X outcomes are being logged with real records" is false. A dashboard or analyst reading this file sees fabricated posts/timestamps. It also destroys the Day-0 measurement baseline the synthesis requires (`SYNTHESIS.md:46`).
- **Smallest fix:** inject the outcome path from config/env (or `self.history_file.parent`) into `_record_x_outcome` and skip recording when `safety.dry_run` is true; then quarantine/truncate the current `data/x_outcomes.json`. Tests' temp dir already exists (`tests/test_x_trend_integration.py:14-17`) — reuse it.

### BLOCKER B2 — X and Bluesky posting loops: 0 successes in 32 post-ship attempts, all evidence/voice-gate rejections

- **Evidence:** `trial_metrics.json` 11-20: `original_post` 21 skipped / 0 success; `bluesky_post` 11 skipped / 0 success. Representative quotes: `:4443-4450` `unsourced number: 4MB; weak voice 6/10: {'pov': 2, 'stakes': 2, 'stance': 0, 'specificity': 2, 'clean_open': 0}`; `:4993-5000` `weak voice 3/10: {'pov': 0, 'stakes': 1, 'stance': 0, 'specificity': 2, 'clean_open': 0}`.
- **Impact:** two of three publishing channels are effectively offline post-ship. The guardrail is correct; the generators (`src/ai_generator.py` hot-take/Bluesky paths feeding `scheduler.py:1701-1731`) cannot satisfy the ≥7/10 voice + zero-unsourced-number rubric (`src/growth.py:323-391`). Stance is 0 in the large majority of rejects. If the release is meant to restore growth, this is a functional failure, not just telemetry.
- **Smallest fix:** make the existing one-shot qualitative regeneration loop apply to X/Bluesky drafts (the LinkedIn path already re-gates at `scheduler.py:2094` and `:2241`), and add `stance` markers to the X/Bluesky prompt. Verify with a dry-run batch that ≥1 draft/10 clears `evidence_gate` before shipping.
- **Caveat:** if the intended scope of this release was *integrity only* (stop bad posts, accept zero volume), downgrade this to a non-blocker — but then do not claim the posting loops are "working."

---

## 7. HYPOTHESES (not confirmed)

1. **X session auth flapping.** `X browser session not authenticated; discovery skipped` appears 9 times on 11-20 (`:4413-4420,4473-4480,4533-4540,4603-4610,4663-4670,4723-4730,4783-4790,4843-4850,4943-4950`), yet a real X reply succeeded at `07:02:49Z` (`:4903-4910`), which requires `self.twitter.is_logged_in()` to have returned true at `:862`. Auth was false at 06:02, true at 07:02, false again at 08:02. Could be an intermittently failing Playwright session check, expired cookies, or a transient each run. **Cannot distinguish without GitHub Actions logs.** If false-negatives, ~9 reply opportunities/day are being lost.
2. **Discovery starvation.** 9 skips for "No high-engagement [unreplied|unquoted] trending tweet found" may reflect a real absence of qualifying targets, or the narrow `GROWTH_ACCOUNTS` sampling (`scheduler.py:856`) + already-used-set filtering. No discovery log exists (`research/xbsky-x-replies.md:144` explicitly recommends one).
3. **Bluesky reply at 02:24Z** may be from a local/manual run rather than cloud: it does not align with the 6-hour cron (`x_automater.yml:6`) and has no corroborating state file. Timeline only, not proof.

---

## 8. UNVERIFIABLE / cannot check

- **GitHub Actions run history and step logs** — no credentials/GitHub CLI access. Cannot confirm any workflow actually executed on 11-20, whether `linkedin-peers` ran, or whether failures were masked by `continue-on-error: true` (`x_automater.yml:79,115`).
- **Actual reach/engagement** — no platform analytics. `growth_baseline.json:1-3,92-97` explicitly says impressions/profile views are not captured; `linkedin_profile.json` zeros are scraper defaults. No follower history (`data/x_followers.json` absent).
- **48 h / 7 d outcome values** — `data/linkedin_outcomes.json` metrics are due `2026-11-22T06:02:19Z`, i.e. in the future relative to this audit. Nulls are correct; whether they get filled later **cannot be verified now**.
- **LinkedIn engagement workflow** — empty history today, but `SYNTHESIS.md:78` allows a 7-day window. Verdict on that channel is deferred, not "failed."
- **Lifetime counters** in `trial_metrics.json:7-20` (1854 cycles, 299 original successes, 26 reply successes, etc.) — cumulative since `2026-10-21T21:41:38Z`; `recent_events` is capped at 500, so these totals cannot be reconciled or attributed to the post-ship change. **No win may be claimed from them.**
- **Live browser / Playwright state** — not available; the 11-15 "Executable doesn't exist" failures (`trial_metrics.json:49`) are historical and no equivalent failure occurs on 11-20.

---

## 9. Claims that are NOT supported by the data

- "Posting loops are producing successes" — true only for LinkedIn (1). False for X and Bluesky (0/32).
- "Reply loops are healthy" — 1 X reply and 1 Bluesky reply; LinkedIn engagement zero; 16 X reply skips. At best marginal.
- "Outcome files are being created with real records" — true for `data/linkedin_outcomes.json` only. False for `data/x_outcomes.json` (100% fixtures).
- "Cap/cooldown fix confirmed" — true for LinkedIn 1/day + 720 m. Not evidence for the other platforms.
- "Growth/engagement improved after the change" — unsupported. No analytics, no engagement records, no follower data.
- "No failures post-ship" — technically true for the 64 logged events (0 `failed`), but 61 were skips; a `skipped` event is not a success.

---

## 10. Blocker / non-blocker summary

**Blockers**
1. **B1** — `data/x_outcomes.json` is entirely local test-fixture data, actively appended by pytest into the production state path (`src/scheduler.py:1733,1521-1527`; `tests/test_x_trend_integration.py:25,34,76,89,100,125,138`). Fix path injection + dry-run guard; quarantine the file.
2. **B2** — X and Bluesky posting loops: 0/32 post-ship successes, all evidence/voice-gate rejects (`trial_metrics.json` 11-20 events; `src/growth.py:323-391`). Fix generator/regeneration, or explicitly descope volume claims.

**Non-blockers**
- **N1 (confirmed win):** LinkedIn cadence fix works — exactly 1 post, 720 m cooldown honored, 1/1 daily cap enforced (`trial_metrics.json:4393-4710,4763-4770,4823-4990`; `config.py:59,67`).
- **N2 (confirmed win):** real LinkedIn outcome record with real URN and correct future `measure_due_at` (`data/linkedin_outcomes.json:5-16`), cross-checked against `linkedin_post_history.json:1206-1215`.
- **N3:** one corroborated real X reply (`post_history.json:533`); one uncorroborated Bluesky reply event.
- **N4:** pre-ship total counter overshoot `25/20` (`trial_metrics.json:4363-4380`); minor, outside window.
- **N5:** `data/bluesky_outcomes.json` and `data/x_followers.json` absent though referenced by the workflow (`x_automater.yml:149,156`); measurement gap, not a post-ship regression.
- **N6:** `linkedin_engagement_history.json` empty — decision deferred to the 7-day kill criterion (`SYNTHESIS.md:78`).

**Re-check trigger:** after B1/B2 are fixed, re-run this audit on the next cloud cycle and confirm ≥1 non-LinkedIn original post clears the gate, `data/x_outcomes.json` contains only real cloud posts, and `linkedin_engagement_history.json` grows within 7 days of 2026-11-20.
