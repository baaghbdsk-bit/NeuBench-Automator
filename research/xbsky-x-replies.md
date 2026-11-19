# X replies — mechanical root-cause report

Role: `x-reply-engineer` (`agents/x-reply-engineer.md`). Scope: why 0/39 replies succeeded, what is actually broken, the smallest fixes, and what to log. Date: 2026-11-20.

**Production code was not modified.** This file is the only artifact written.

---

## 0. Bottom line

| | Finding |
|---|---|
| **1** | The "no high-engagement target" skip is **not** an engagement-threshold decision. `_pick_trending_target` has no threshold at all (`src/scheduler.py:832-880`); the skip at `src/scheduler.py:891-902` fires only when discovery returned **zero usable URLs**. The 35 skips each burned **193-197 s** (`trial_metrics.json` `duration_s`) — they are browser-discovery timeouts, not instant rejections. |
| **2** | Discovery is browser scraping with no session check and no per-source telemetry. `is_logged_in()` exists (`src/twitter_client.py:172`) but is called **nowhere** in the repo. Both discovery methods drop every row unless `[data-testid="tweetText"]` yields >10/>15 chars plus a `/status/` link (`src/twitter_client.py:543,654`). One broken session or one DOM rename zeroes both paths, and nothing is logged. |
| **3** | Even when a target *is* found, confirmation is unreliable: 3 events ended "X reply submission timed out; retry blocked to prevent duplicates", and **8** reservations remain `status: unknown` forever (`post_history.json` `pending_x_actions`; e.g. `:790-821`). A target that times out is permanently un-replyable (`src/x_state.py:279-283`). |

**Strongest recommendation:** stop shipping `python main.py reply` as an auto-discovery loop. Feed exact, curated, on-niche tweet URLs through the already-supported `python main.py reply --url …` path (`main.py:173-177`, `src/scheduler.py:435-516`), fix confirmation truthiness, and require **one verified success** before any further reply work. Treat auto-discovered "viral sniper" replies as retired, not pending repair.

**Biggest uncertainty:** I cannot determine *why* discovery returns zero — stale/absent X session cookies vs X DOM/selector drift vs search throttling — because this workspace has no `browser_session/cookies.json`, no Python/Playwright runtime, no credentials, and no GitHub Actions logs. Those are hypotheses, not findings.

---

## 1. Method and explicit limits

What I did:
- Read `agents/README-X-BLUESKY.md`, `agents/x-reply-engineer.md`, `src/scheduler.py`, `src/twitter_client.py`, `src/x_state.py`, `src/tracker.py`, `src/safety.py`, `config.py`, `main.py`, `.github/workflows/x_automater.yml`, `tests/test_x_trend_integration.py`.
- Parsed all 500 `recent_events` in `trial_metrics.json` and the X keys in `post_history.json` (PowerShell `ConvertFrom-Json`).
- Recovered historical `src/scheduler.py` blobs from loose `.git/objects` with a PowerShell zlib/Deflate reader, because no `git` binary is installed on this machine.

What I **could not** test locally (so I do not claim it):
- No usable Python (only the Windows Store stub; no `venv`), no Playwright browsers, no `browser_session/cookies.json` (verified absent), no X credentials. I never called `is_logged_in()`, `search_public_tweets()`, `get_top_tweets_from_account(s)()`, or `post_reply()` against live X.
- No GitHub Actions run logs in the workspace, so I cannot prove which commit SHA was live at each 6 h run.
- The current working tree contains a batch profile scan (`src/twitter_client.py:562-613`) wired into `_pick_trending_target` (`src/scheduler.py:842-854`). Per the manager it **has not run in production**; I do not credit it as a fix. Git objects show a form of it entered the repo by the CI commit `dfabb6f` (2026-11-19 ~15:41 UTC), but no logged success follows it.

---

## 2. Exact reply path

| Stage | Code | What happens |
|---|---|---|
| Schedule | `.github/workflows/x_automater.yml:6` | `cron: '0 */6 * * *'`. |
| Step selection | `x_automater.yml:114-144` | Alternate by `HOUR % 4`; `python main.py reply` at `:142` (or `repost` at `:135`). Steps are `continue-on-error: true` (`:79`, `:115`). |
| CLI dispatch | `main.py:173-179` | `run_single_cycle(force_action="reply")`; `sys.exit(1)` on failure. |
| Guard | `src/scheduler.py:738-783`, `src/safety.py:65-71` | Trial/cap checks; cap is 12/day in workflow (`:123`) vs config default 24 (`config.py:137`). |
| Dispatch | `src/scheduler.py:797-805` | `_execute_sniper_reply`; on failure falls back to an original post unless outcome is `unknown`. |
| **Discovery** | `src/scheduler.py:832-880` | Batch profile scan, then 8 search queries; dedupe against `replied_urls`. |
| Skip | `src/scheduler.py:891-902` | Emits exactly `"No high-engagement unreplied trending tweet found"`. |
| Generation | `src/scheduler.py:909-937` | `generate_sniper_reply(target_account, tweet_text)`. |
| Reservation | `src/scheduler.py:945-965`, `src/x_state.py:197-233` | `reserve_target`; rejects already-completed/reserved URLs. |
| Submission | `src/twitter_client.py:292-356` | Playwright click reply → type → click post → wait for confirmation. |
| Confirmation | `src/twitter_client.py:94-128` | Listener accepts only a response URL containing `CreateTweet` with status 200, or narrow toast phrases. |
| Finalize | `src/scheduler.py:973-1008`, `src/x_state.py:236-286` | `success` / `failed` / `unknown`; `unknown` is kept blocked forever. |

The same `_pick_trending_target` drives quote-tweets with `reposted_urls` (`src/scheduler.py:1012-1032`) — 10/12 quote-tweets skipped for the parallel reason "No high-engagement unquoted trending tweet found". This is corroboration that the *shared discovery function* is the fault line, not reply text generation.

---

## 3. Confirmed root causes

### C1 — The skip means "zero candidates", not "low engagement"

- `_pick_trending_target` selects `best` by `engagement_score` but **never compares it to a threshold** (`src/scheduler.py:848-854`, `:868-874`). A score of 0 (which `_tweet_engagement` returns when labels are absent — `src/twitter_client.py:41-53`) is accepted. `best` is returned as-is at `:878-880`.
- Therefore the only way to reach `src/scheduler.py:892-902` is `best is None`: every discovery source returned no URL, or every URL was already in `replied_urls`.
- Data: 35/39 reply events carry that exact reason (`trial_metrics.json` reply events; representative lines `:2469`, `:2519`, `:4959`); 36 skipped, 3 failed, **0 success** in the 500-event window.
- Duration: all 35 skips took **193.43-197.84 s** (mean ≈195 s). An instant reject (dedupe of a nonempty list, cap, threshold) would be ~0 s. ~195 s is the signature of exhausting 8 sequential browser-backed lookups.

**Conclusion:** the label is misleading. There is no "high-engagement" filter to relax. Relaxing it would change nothing.

### C2 — Discovery is browser scraping with no session check and no telemetry

- `search_public_tweets` (`src/twitter_client.py:615-671`) launches a browser per query, loads `https://x.com/search?q=…&f=live` (`:621`, `:629`), waits 3 s (`:630`), waits up to 8 s for `article[data-testid="tweet"], article` (`:632`), and keeps a row only if `len(tweet_text) > 15` (`:654`). It catches every exception and returns `[]` with only a `print` (`:665-666`).
- `get_top_tweets_from_account` (`src/twitter_client.py:517-560`) and the batch variant (`:562-613`) have the same gates: `article` wait (`:531-534`, `:582-585`), `[data-testid="tweetText"]` (`:538-539`, `:590-591`), `/status/` link (`:540-542`, `:592-594`), and `len(text) > 10` (`:543`, `:595`). All failures are swallowed into `[]` or a `print`.
- `_get_context_and_browser` (`src/twitter_client.py:130-155`) trusts `storage_state=cookies.json` if the file exists. The workflow restores it from `X_COOKIES_BASE64` (`x_automater.yml:65-76`). There is **no** call to `is_logged_in()` before any of this — that method is defined at `:172` and referenced nowhere else in the repository.
- The console notes printed by the catch blocks (`"Trending search note: …"`, `"Could not read @user: …"`) are not persisted anywhere; `trial_metrics.json` stores only the final skip reason and duration (`src/tracker.py:171-188`).
- Historical evidence from git objects: the production-era revision (`dc7529c`, `8da9003`, 2026-11-17/19 UTC) sampled **8 `VIRAL_ACCOUNTS`** through `get_top_tweets_from_account` (one browser per account) and its fallback queries were `"Ramayana", "Bollywood", "AI", "Indian cinema", "ChatGPT", "tech"` — off-niche per `agents/README-X-BLUESKY.md:13-14`. The ~195 s per skip matches eight browser launches/navigation timeouts plus eight searches. The working tree later replaced these with 6 `GROWTH_ACCOUNTS` + 2 `VIRAL_ACCOUNTS` and AI queries (`src/scheduler.py:137-163`, `:836-838`, `:862-865`); that change is unproven in production and is not a fix.

**Conclusion:** discovery can fail in total silence, and the system has no way to distinguish "no tweets exist" from "session dead" or "selector renamed".

### C3 — Confirmation is a second, independent failure mode; targets get locked

- `post_reply` sets `submission_started = True` **before** clicking (`src/twitter_client.py:326-334`). If no `CreateTweet` 200 response and no matching toast arrive within 15 s, it returns `unknown` (`:336-346`).
- Data: 3 reply events ended "X reply submission timed out; retry blocked to prevent duplicates" (2026-11-18T06:20, 2026-11-18T09:21, 2026-11-19T18:12 UTC; 86-107 s each). Their targets are viral-account URLs that match `pending_x_actions` entries with `reserved_at` 30-90 s earlier (`post_history.json`).
- `complete_reservation` with `outcome="unknown"` keeps the entry with `status: unknown` (`src/x_state.py:279-283`), and `reserve_target` blocks any future reply to that URL via `_pending_match` (`:144-160`, `:213-218`). One logged skip is exactly `"This X reply target is already completed or reserved."`
- State: **8** `pending_x_actions` remain, all `unknown` (6 reply, 2 repost). So even a rare discovery success can be permanently wasted by an unconfirmed submission.
- The `unknown` path is deliberate (prevents duplicates) — the bug is that there is **no reconciliation step** that checks X for the published reply and clears the reservation.

### C4 — CI cannot distinguish a dead loop from a working one

- The reply step is `continue-on-error: true` (`x_automater.yml:115`), and `main.py:178-179` exits 1 on failure. So 39/39 unsuccessful attempts leave the workflow **green**; `🚨 Alert on Failure` (`:215`) never fires.
- `lifetime_summary` (`trial_metrics.json`) shows `replies_attempted: 144`, `replies_succeeded: 25` — those 25 successes predate the current 500-event window (earliest event 2026-11-14T21:48 UTC), so they do not contradict the 0/39 recent record. They most likely came from older revisions/direct-URL runs; the current window has no reply success at all.
- Event schema has no fields for source, candidate count, session state, response status, or verified outcome (`src/tracker.py:171-180`). There is nothing to alert on.

### C5 — Secondary: dedupe and off-niche targets

- `replied_urls` holds 28 URLs (`post_history.json`). It is applied at `src/scheduler.py:834` and `:850`/`:870`. With 0 recent successes it cannot explain 35 zero-result runs, but it did produce one skip and permanently blocks the 8 unknown reservations.
- Stuck reservations contain off-niche drafts, e.g. "unhinged reply guy with an anime PFP" (`post_history.json:795`), "okra … #Swiggy" (`:806`), "Netflix … #AI #TechTrends" (`:817`) — violating the niche rule (`agents/README-X-BLUESKY.md:13-14`). Even if discovery were repaired, these targets would convert a no-op into a liability.

---

## 4. Ruled out (with evidence)

| Suspect | Verdict | Evidence |
|---|---|---|
| Engagement threshold too high | **No threshold exists** | `src/scheduler.py:848-854`, `:868-874`, `:878-880`. |
| Daily caps / trial guard | Guards passed | A cap skip would carry the cap reason from `src/safety.py:53-71`; the 35 skips proceeded past `src/scheduler.py:738-783` into `_execute_sniper_reply`. |
| Rate limits | Not detected | `rate_limits_encountered: 0` in `trial_metrics.json`; no reply reason mentions 429/limit. |
| Empty account list | No | `GROWTH_ACCOUNTS` (25) and `VIRAL_ACCOUNTS` (30) are nonempty (`src/scheduler.py:97-163`); production-era code sampled 8. |
| `NameError` from `best["target_account"] = t` | **Rejected** | I initially suspected this from a truncated git dump. Reading the full function shows `best["target_account"] = target_account` in every revision, including `dc7529c`. No such bug. |
| "Batch scan is the fix" | **Not credited** | Per manager, unproven in production; no logged success after it entered the repo. |

---

## 5. Hypotheses (cannot be confirmed locally)

| # | Hypothesis | Exact mechanism | What would prove it |
|---|---|---|---|
| H1 | Stale/absent X session | `X_COOKIES_BASE64` missing or expired → `x.com` serves login wall → no `article` nodes → 8 s wait timeout per lookup; ~195 s total. | Log `login_check_result=false` and `final_url` containing `/login` at stage 2. |
| H2 | Selector drift | `[data-testid="tweetText"]` and/or `article[data-testid="tweet"]` renamed, or the author/status link moved → `article` found but `text` empty → all rows dropped by `len(text)>10` (`:543`) / `>15` (`:654`). | Log `articles_seen>0` with `tweets_passing_text_gate=0` and a one-off DOM sample of the first article. |
| H3 | Search throttling / anonymous search gate | `&f=live` search is login-gated or rate-limited for this session; exception swallowed at `src/twitter_client.py:665`. | Log per-query HTTP status / exception text and `final_url`. |
| H4 | Random account sampling hits dead accounts | 8 random viral handles include blocked/suspended/empty profiles; `src/twitter_client.py:527-528` silently returns `[]`. | Log per-handle `tweets_seen` and `skip_reason` for each of the 8 accounts. |

These are not mutually exclusive. The 3 "unknown" events show discovery *sometimes* returned a target, so total selector breakage (H2 as a single global cause) is unlikely; intermittent session/throttle/account-state issues are more consistent with the observed pattern. I cannot test any of them here.

---

## 6. Ranked fixes (impact × ease, each with its "useless if")

| Rank | Change | I×E | Useless if … |
|---|---|---|---|
| 1 | **Log discovery** (§7) before the skip: per-source counts, session state, exception text, final URL. Add `deployed_sha`. | 5×5 | … the log records only the final skip (current behaviour); you still cannot separate H1-H4 and will burn ~195 s ×4/day indefinitely. |
| 2 | **Replace auto-discovery with curated `reply --url` input** from an on-niche list of exact tweet URLs; the path already exists at `main.py:173-177` / `src/scheduler.py:435-516`. Remove `python main.py reply` (auto) from `x_automater.yml:137-143` until a verified success exists. | 5×4 | … the curated URLs are old, off-niche, or on mega-threads where a small account is buried; or confirmation still returns `unknown` and locks each URL (C3). Pair with #1 and #3. |
| 3 | **Reconcile `unknown` submissions**: on `unknown`, make one bounded check of the target page for a reply from our own handle; clear the reservation only on positive match, otherwise mark `failed_unverified` with a visible alert. Do not auto-retry blindly. | 4×3 | … the check reuses the same `CreateTweet`-only listener that failed, or auto-retries without idempotency (duplicate reply). Must use an independent verification source. |
| 4 | **Fail fast on session**: call the existing `is_logged_in()` (`src/twitter_client.py:172`) once per cycle; if false, record a distinct skip and stop before the 8 browser launches. | 5×2 | … `is_logged_in()` itself depends on the same selectors that may have drifted, giving a false "logged out"; or the check passes but search is still throttled. |
| 5 | **Keep the current AI-niche account list and queries** (`src/scheduler.py:137-163`, `:836-865`) and never restore the production-era `"Ramayana"/"Bollywood"/"Indian cinema"` fallback. | 4×1 | … discovery still returns zero; a cleaner query list changes nothing when the session/DOM is broken. Cheap hygiene, not a win. |
| 6 | **Do not credit/scale the batch profile scan** (`src/twitter_client.py:562-613`) until it has a logged success. | 3×5 | … H1/H2/H3 hold; it returns `[]` just as fast, and its only failure output is a dim console note (`src/scheduler.py:842-846`). Its random 2 viral accounts can still pick off-niche targets. |
| 7 | **Retire X replies as a growth channel**; redirect effort to on-niche original posts and the measurable Bluesky reply loop. | 5×2 | … you also drop outcome measurement; keep the log so the decision is reversible with evidence. |

Impact/ease are 1-5; score is the product. Rank 2 is the actionable fix, rank 1 is its prerequisite, rank 7 is the decision.

---

## 7. Logging spec

Append one JSON line per stage to a new append-only file, e.g. `data/x_reply_discovery.jsonl`. Do **not** rely on `trial_metrics.json.recent_events` — it is capped at 500 (`src/tracker.py:184-188`) and today stores only `reason` + `duration_s` (`:171-180`).

Per cycle (one row at start):
```
ts_utc, run_id, deployed_sha (GITHUB_SHA), action, dry_run,
cookies_file_exists, cookies_mtime_utc, login_check_result, login_final_url
```

Per discovery source (one row per handle/query, including zero-result ones):
```
run_id, source (profile_batch|profile_single|search|curated_url),
query_or_handle, http_status, final_url, exception_type, exception_message,
elapsed_ms,
articles_seen, tweets_with_status_link, tweets_with_text,
tweets_passing_length_gate, engagement_scores[],
discard_reasons[]  (one of: login_wall, no_article, no_text, no_status_link,
                    too_short, dedupe, blocked_profile, exception)
```

Per accepted candidate:
```
run_id, tweet_url, target_handle, engagement_score, niche_ok (bool),
tweet_age_minutes, already_used (bool), accepted (bool), score_source
```

Per submission:
```
run_id, reservation_id, submission_started (bool),
create_tweet_response_url, create_tweet_http_status, toast_text[],
confirmation_method (response|toast|page_check), confirmed (bool),
final_outcome (success|failed|unknown), verified_reply_url, pending_after
```

Per final event (extend the existing `record_event` payload):
```
discovery_summary: {
  sources_attempted, sources_returning_zero, candidates_seen,
  candidates_accepted, candidates_rejected_dedupe, total_discovery_ms
}
```

Alert/kill thresholds derived from the log:
- `login_check_result=false` → hard skip in <5 s, never spend 195 s.
- `sources_returning_zero == sources_attempted` for 3 consecutive runs → page/alert; stop the 6 h loop until diagnosed.
- `final_outcome=unknown` > 0 in any 24 h → block scaling and require reconciliation (#3).
- `pending_x_actions` with `status=unknown` > 0 → no new replies until drained.
- Any `niche_ok=false` accepted candidate → stop replies immediately (charter constraint).

---

## 8. Should replies be abandoned as a growth channel?

**Yes — auto-discovered X replies should be abandoned now.** 0/39 with 35 zero-candidate skips, ~195 s burned per no-op, 8 permanently locked targets, no outcome data, and off-niche roast drafts that violate the charter. Repairing scraping is not enough: even a working scraper would feed a small personal account replies into mega-threads where they are buried, with no measurement to prove value.

A *different* tactic — a small, curated, on-niche `reply --url` pilot with verified success — can be run as an experiment, not as a growth plan. Gate it on one confirmed reply and a real outcome log; if that gate is not met within 7 days, retire the channel entirely and report "no evidence of effect" rather than manufacturing activity.

---

## 9. Return block

- **Top 3 findings:** (1) "No high-engagement target" is a misnomer — no threshold exists; it means zero discovery candidates, and each skip costs ~195 s (`src/scheduler.py:832-880,891-902`; `trial_metrics.json` 35 × 193-197 s). (2) Discovery is silent browser scraping with no session check: `is_logged_in()` is dead code, and all row-drop reasons are swallowed into console `print`s (`src/twitter_client.py:130-172,517-671`). (3) Confirmation is unreliable and permanently locks targets: 3 `unknown` events, 8 stuck `pending_x_actions` (`src/x_state.py:279-283`).
- **Strongest recommendation:** retire auto-discovery; feed curated on-niche URLs through `python main.py reply --url`, reconcile `unknown` outcomes, and require one verified success before resuming. Instrument discovery first (§7).
- **Biggest uncertainty:** whether zero results are caused by stale X cookies, selector drift, or search throttling. No local browser session, credentials, Playwright runtime, or Actions logs — every specific mechanism remains a hypothesis (§5).
