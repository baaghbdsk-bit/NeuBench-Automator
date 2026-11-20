# Final Validation — Workflows & Cloud Execution (WORKFLOWS angle)

**Scope:** all four files in `.github/workflows/`, parsed with PyYAML (not just read as text), cross-checked against `config.py`, `src/safety.py`, `src/scheduler.py`, `src/tracker.py`, `src/ai_generator.py`, `main.py`, and the on-disk state files.
**Evidence cut:** 2026-11-20, local checkout at `D:\x-linkdin-bluesky\NeuBench-Automator`.
**Method:** verify claims against the YAML and the code paths the YAML invokes; do not modify production code; no metrics invented.

---

## Verdict: **FIX FIRST**

Two workflow-level defects are shippable blockers on their own, independent of the content/generator blockers already recorded in `research/final-cloud-evidence.md`:

1. The primary scheduled workflow (`x_automater.yml`) cannot fail: both action steps are `continue-on-error: true`, so a run that publishes **nothing** is green and its `failure()` alert never fires. Given the measured 0/32 post-ship successes in `final-cloud-evidence.md`, this is not hypothetical.
2. The same workflow's state-persistence step swallows every git failure (no retry, no conflict strategy, all commands `||`-masked), so outcome logs and engagement history can be silently lost on a normal concurrent push.

---

## 1. Parsed workflow inventory

| Workflow | Trigger (UTC) | Concurrency group | Timeout | Action step `continue-on-error` | State files committed |
|---|---|---|---:|---|---|
| `x_automater.yml` | `0 */6 * * *` (00/06/12/18) | `omnichannel-state-sync`, `cancel-in-progress: false` | 25 min | **yes** (`:79`, `:115`, `:148`) | `post_history.json`, `trial_metrics.json`, `linkedin_network.json`, `linkedin_post_history.json`, `linkedin_engagement_history.json`, `data/x_followers.json`, `data/linkedin_outcomes.json`, `data/bluesky_outcomes.json`, `data/x_outcomes.json` (`:156`) |
| `linkedin_automater.yml` | manual only (`workflow_dispatch`) | `omnichannel-state-sync`, `cancel-in-progress: false` | 20 min | no | `linkedin_post_history.json`, `trial_metrics.json`, `linkedin_engagement_history.json` (`:96`) — **missing `data/linkedin_outcomes.json`** |
| `linkedin_engagement.yml` | `30 */3 * * *` (00:30, 03:30, …) | `linkedin-engagement`, `cancel-in-progress: false` | 20 min | no | `linkedin_engagement_history.json` only (`:88`) — **missing `trial_metrics.json` / `post_history.json`** |
| `bluesky_engagement.yml` | `15 */3 * * *` (00:15, 03:15, …) | `bluesky-engagement`, `cancel-in-progress: false` | 15 min | no | `post_history.json`, `trial_metrics.json` (`:73`) |

All four have `permissions: contents: write` (needed for the state push) and no `push` trigger; commits use `[skip ci]`, so no self-trigger loop. Dispatch inputs propagate correctly on schedule (`inputs.dry_run || 'false'`, `inputs.action || 'auto'`). All `action` choice values are valid `main.py` choices (`main.py:84-92`; `auto` is mapped to `post-all` in the shell at `x_automater.yml:99-112`). Secrets referenced: `GEMINI_API_KEY`, `GEMINI_MODEL` (literal, not a secret), `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`, `LINKEDIN_COOKIES_BASE64`, `X_COOKIES_BASE64`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

---

## 2. Cap / cooldown comparison — config defaults vs workflow overrides

| Setting | `config.py` default | `x_automater.yml` | `linkedin_automater.yml` | `linkedin_engagement.yml` | `bluesky_engagement.yml` |
|---|---:|---:|---:|---:|---:|
| `MAX_DAILY_TOTAL` | 20 (`safety.py:28`) | **20** (`:96`) | **0** (`:77`) | **0** (`:75`) | **0** (`:55`) |
| `MAX_DAILY_X_ORIGINALS` | 4 (`config.py:136`) | 4 (`:91`) | 0 (`:74`) | 0 (`:72`) | 0 (`:56`) |
| `MAX_DAILY_X_REPLIES` | 24 legacy / 12 via `MAX_DAILY_X_REPLIES` (`config.py:137`) | 12 (`:92`) | 0 (`:75`) | 0 (`:73`) | 0 (`:57`) |
| `MAX_DAILY_X_REPOSTS` | 6 legacy / 4 (`config.py:138`) | 4 (`:93`) | 0 (`:76`) | 0 (`:74`) | 0 (`:58`) |
| `MAX_DAILY_LINKEDIN` (posts) | 1 (`config.py:59,132`) | 1 (`:94`) | 1 (`:78`) | **0** (`:70`) | 0 (`:60`) |
| `MAX_DAILY_BLUESKY` | 4 (`config.py:139`) | 4 (`:95`) | — | — | 0 (`:59`) |
| `MAX_DAILY_LINKEDIN_PEER_COMMENTS` | 6 (`config.py:133`) | — (default 6) | — | 6 (`:71`) | — |
| `LINKEDIN_MIN_INTERVAL_MINUTES` | 720 (`config.py:67`) | 720 (`:97`) | 720 (`:79`) | — | — |
| `LINKEDIN_SCHEDULE_GRACE_MINUTES` | 60 (`config.py:68`) | default 60 | 60 (`:80`) | — | — |
| `GEMINI_MODEL` | `gemini-3.5-flash` (`config.py:15`) | `gemini-2.5-flash` (`:82`, `:119`) | `gemini-3.5-flash-lite` (`:67`) | `gemini-3.5-flash-lite` (`:62`) | `gemini-2.5-flash` (`:47`) |

**Checked and correct:** a cap of `0` means *unlimited/disabled*, not "zero allowed" — every enforcement site is guarded by `limit > 0` / `max_daily_total > 0` (`safety.py:53,62,70,78,86,97`; scheduler `:2466-2468`, `:2540-2543`). So the engagement workflows' `MAX_DAILY_TOTAL: '0'` does **not** block them, and the comment at `bluesky_engagement.yml:53-54` is accurate. Their peer-comment cap of 6 is enforced from `linkedin_engagement_history.json` (`scheduler.py:2537-2543`), which **is** committed by that workflow. No config/workflow cap contradiction found.

**Unchecked interaction (confirmed in code, impact uncertain):** `tracker.get_today_counts()` increments `total_actions` for *every* successful event regardless of action type (`tracker.py:111-115`), including `bluesky_reply` and `linkedin_peer_comment`. `bluesky_engagement.yml` commits `trial_metrics.json`, so its successful replies count toward the **next** `x_automater` run's `MAX_DAILY_TOTAL=20` budget (`scheduler.py:2372-2387`, `:751-753`). The "isolated lane" is therefore only isolated within its own process. Eight Bluesky replies/day plus omnichannel broadcasts can push the shared counter past 20 and starve a later broadcast — and because of BLOCKER W1 that starvation is silent.

---

## 3. CONFIRMED issues

### BLOCKER W1 — `x_automater.yml` can run successfully while doing nothing, and cannot alert

- **Evidence:** `x_automater.yml:79` (`Execute Autonomous Broadcast Cycle` → `continue-on-error: true`), `x_automater.yml:115-116` (Sniper step → `continue-on-error: true`, gated only by `always()`), `x_automater.yml:148` (snapshot → `continue-on-error: true`). The alert step is `if: failure()` at `x_automater.yml:198`. `main.py:162-163` exits 1 when `run_six_hour_omnichannel_cycle()` returns all-`False`; the same `sys.exit(1)` pattern applies to `post` (`:170-171`), `reply` (`:178-179`), `repost` (`:186-187`), `linkedin` (`:206-207`), `linkedin-peers` (`:214-217`), `bluesky` (`:224-225`), `bluesky-replies` (`:228-230`). With `continue-on-error`, a step-level failure does **not** set the job to failure, so `failure()` is false and no Telegram alert is sent.
- **Also masked:** a Gemini outage/invalid model raises `RuntimeError("All Gemini models failed…")` (`ai_generator.py:163-192`); `run_six_hour_omnichannel_cycle` catches it with a bare `console.print` (`scheduler.py:2407-2408`, `:2415-2416`, `:2423-2424`) and records **no** event, so even the run summary's outcome list stays empty. A run with a dead API key is indistinguishable from a healthy one.
- **Impact:** the flagship 4×/day workflow reports green with zero publishes and zero notification. Corroborated operationally by `research/final-cloud-evidence.md:104-109` (0/32 post-ship X/Bluesky successes) and `:88` (pre-ship `Total daily limit reached (25/20)` gating at `x_automater.yml:96`).
- **Smallest fix:** remove `continue-on-error: true` from `:79` and `:115` (keep it only on `:148`, which is explicitly best-effort). If the intent is to tolerate platform-specific failures while still catching "nothing happened", instead capture the step outcome and add an explicit `if: failure() || steps.automater.outcome == 'failure'` alert plus a post-step check on `steps.*.outcome`, and record a `failed` event in the exception handlers at `scheduler.py:2407-2424`.

### BLOCKER W2 — `x_automater.yml` state push is best-effort only; outcome logs can be silently lost

- **Evidence:** `x_automater.yml:161-163`:
  ```
  git commit -m "... [skip ci]" || echo "No changes to commit"
  git pull --rebase --autostash origin main || true
  git push origin main || echo "Push skipped or non-fast-forward"
  ```
  No commit guard, no retry loop, no conflict strategy, and every failure is masked. If the pull conflicts, the repo is left mid-rebase and `git push` fails; the step still exits 0. It is also the **only** workflow that commits `data/linkedin_outcomes.json`, `data/bluesky_outcomes.json`, `data/x_outcomes.json` and `data/x_followers.json` (`:156`). Contrast `linkedin_automater.yml:107-121` and `linkedin_engagement.yml:99-113`, which retry 3× with `sleep 5` and `exit 1` if the push never succeeds.
- **Impact:** a lost push loses the day's outcome records, dedupe keys (`post_history.json`), engagement history, and counter events (`trial_metrics.json`). It runs concurrently with `bluesky_engagement.yml` and `linkedin_engagement.yml` (different concurrency groups), so non-fast-forward pushes are a normal occurrence, not an edge case. Downstream caps then under-count and duplicate posts/replies become possible.
- **Smallest fix:** reuse the proven pattern from `linkedin_engagement.yml:98-113` in `x_automater.yml` (commit guard + 3× `git pull --rebase --autostash -X theirs` + `git push` + `exit 1` on exhaustion). Do not leave `|| true` on the pull.

### NON-BLOCKER W3 — `linkedin_engagement.yml` writes tracker state it never commits

- **Evidence:** `linkedin-peers` calls `tracker.record_event()` (`scheduler.py:2545-2552`, `:2558-2565`, `:2629-2636`), and `record_event()` calls `save()` (`tracker.py:195`), which writes **both** `trial_metrics.json` and `post_history.json` (`tracker.py:89-90`). But the workflow's persist step stages only `linkedin_engagement_history.json` (`linkedin_engagement.yml:88`).
- **Impact:** those events never reach `main`; they are overwritten by the next workflow that commits its own checkout of `trial_metrics.json`. Global-cap accounting and the run-summary outcome list under-report LinkedIn engagement. The cap itself is unaffected because it reads the committed engagement-history file.
- **Smallest fix:** add `trial_metrics.json` and `post_history.json` to the loop at `linkedin_engagement.yml:88`. Note this will make the W2 cap interaction slightly worse (more counted actions) — fix W2/W1 first.

### NON-BLOCKER W4 — `linkedin_automater.yml` does not commit the LinkedIn outcome log it writes

- **Evidence:** successful LinkedIn posts call `_record_linkedin_outcome()` (`scheduler.py:2312-2318`), which writes `data/linkedin_outcomes.json` (`scheduler.py:1786-1812`). The manual workflow's state list at `linkedin_automater.yml:96` omits that path; only `x_automater.yml:156` includes it.
- **Impact:** a manual `workflow_dispatch` post gets no durable measurement record unless a later scheduled run happens to commit it. Local `data/linkedin_outcomes.json` currently holds one real record (`2026-11-20T06:02:19Z`, URN `urn:li:ugcPost:7529423859377197057`), so the gap is latent, not yet user-visible.
- **Smallest fix:** add `data/linkedin_outcomes.json` to `linkedin_automater.yml:96`.

### NON-BLOCKER W5 — `bluesky_engagement.yml` push failure only warns

- **Evidence:** `bluesky_engagement.yml:81` masks commit errors with `|| true`; `:94-95` emits `::warning::` and lets the job succeed after 3 failed pushes. The state includes `post_history.json` with `bluesky_replied_uris` (written at `scheduler.py:2685-2688`).
- **Impact:** lost reply-dedupe state can cause duplicate replies on the next cycle. No failure signal beyond a log warning; there is no alert step in this workflow at all.
- **Smallest fix:** mirror `linkedin_engagement.yml:110-113` (`exit 1` on push exhaustion) and add a failure-alert step if notifications are wanted.

### NON-BLOCKER W6 — no failure alerts in either engagement workflow

- **Evidence:** `bluesky_engagement.yml` and `linkedin_engagement.yml` have no `🚨 Alert on Failure` step, unlike `x_automater.yml:197-215` and `linkedin_automater.yml:151-169`. Combined with `TRIAL_ENABLED: 'true'` and secret-dependent steps, a missing `GEMINI_API_KEY`/`LINKEDIN_COOKIES_BASE64` fails silently from the owner's perspective.
- **Smallest fix:** copy the alert step; or accept as a known gap if Actions email notifications are sufficient.

### NON-BLOCKER W7 — cadence label contradicts cron in `linkedin_engagement.yml`

- **Evidence:** `name:` at `:1` and run summary at `:120` say "Every 6 Hours"; cron at `:7` is `30 */3 * * *` (8×/day). With the 6/day peer-comment cap (`:71`), 7 of 8 runs are expected to skip on cap alone.
- **Impact:** misleading run summaries; no functional failure.
- **Smallest fix:** change the label to "Every 3 Hours" or change the cron to `30 */6 * * *` to match intent.

### NON-BLOCKER W8 — `GEMINI_MODEL` diverges across workflows

- **Evidence:** `x_automater.yml:82,119` and `bluesky_engagement.yml:47` use `gemini-2.5-flash`; `linkedin_*.yml` use `gemini-3.5-flash-lite`; `config.py:15` default is `gemini-3.5-flash`; `.env.example:6` recommends `gemini-3.5-flash-lite`. The fallback chain is built from `config.GEMINI_MODEL` plus two literals (`ai_generator.py:163-167`), so each workflow gets a different first choice.
- **Impact:** inconsistent generation quality; if the chosen id is invalid/retired, fallback may exhaust and (via W1) fail silently. **I could not verify which model ids are currently valid** — see UNVERIFIABLE.
- **Smallest fix:** pin one value in all four workflows to the id known-good for the installed SDK (or remove the per-workflow override and rely on config).

### NON-BLOCKER W9 — shell injection surface in manual topic input

- **Evidence:** `linkedin_automater.yml:83-89` interpolates `${{ inputs.topic }}` into `CMD_ARGS` and executes `eval "python main.py $CMD_ARGS"`. A topic containing `"`/backticks/`$()` is evaluated by the shell.
- **Impact:** arbitrary command execution in a job that holds all publishing secrets and `contents: write`. Trigger is manual-only, so it requires a repo collaborator — low likelihood, but unnecessary.
- **Smallest fix:** pass the topic via an environment variable and use `python main.py linkedin --topic "$TOPIC"` with no `eval`.

### NON-BLOCKER W10 — referenced follower snapshot file is absent locally

- **Evidence:** `x_automater.yml:147-149` runs `scripts/x_follower_snapshot.py`, which unconditionally writes `data/x_followers.json` (`x_follower_snapshot.py:79-91`); the file is in the persist list (`:156`) and summary (`:178-180`), but is absent from `data/` locally.
- **Impact:** no verifiable follower history. Cannot tell whether the step never ran, the cookie secret is unset, or its push was lost by W2.
- **Smallest fix:** fix W2, then confirm `data/x_followers.json` appears after one scheduled run.

---

## 4. HYPOTHESES (not confirmed)

1. **Last-writer-wins on shared JSON state.** `bluesky_engagement.yml:85` and `linkedin_engagement.yml:100` rebase with `-X theirs`. During a rebase, `-X theirs` favours the commit being replayed (the local state), so when two workflows both modify `trial_metrics.json`/`post_history.json`, the second pusher's whole-file version can discard the first's events. This is inherent to whole-file JSON state; I could not exercise git here (no `git` executable in this environment) to confirm the flag behaves as expected through `git pull --rebase`.
2. **Global-cap overshoot.** `research/final-cloud-evidence.md:88` records `Total daily limit reached (25/20)` before gating. The cap is checked against a counter that already includes all successful events (`tracker.py:111-115`), so the limit is soft and can be exceeded by concurrent steps before the next check. Workflow env (`MAX_DAILY_TOTAL: '20'`) matches config intent; the overshoot is a code/ordering issue, not a wrong env value.
3. **Shallow clone + rebase.** `fetch-depth: 1` in all four workflows. I did not find a concrete failure mode (the merge base is the parent of the local commit and is present), so I am not flagging it.

---

## 5. UNVERIFIABLE / explicitly not checked

- **GitHub Actions run history and step logs** — no credentials, no GitHub CLI, and `git` is not on `PATH` in this environment. I cannot confirm that any of the four workflows actually executed on 2026-11-20, nor which job produced which state file, nor whether `continue-on-error` masked specific failures.
- **Actual commits / pushes to `main`** — no git executable, so I cannot verify the `[skip ci]` commits exist remotely. I verified only that the scripts *would* stage and commit the listed files and how they handle push errors.
- **Secrets are configured** — cannot inspect GitHub repo secrets. Missing `GEMINI_API_KEY`, `LINKEDIN_COOKIES_BASE64`, `X_COOKIES_BASE64`, `BLUESKY_*` would each cause a skip/failure that W1 can hide.
- **Validity of `gemini-2.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.8-flash`** — no API access; model-id correctness is unverified.
- **Live browser / Playwright session / platform APIs / analytics** — not available.
- **Outcome values** — `measure_due_at` for the one LinkedIn record is 2026-11-22, so whether metrics get backfilled later cannot be checked now.

---

## 6. Blocker / non-blocker summary

**Blockers**
- **W1** — primary scheduled workflow is fail-open: `continue-on-error: true` on both action steps (`x_automater.yml:79,115`) plus `if: failure()` alert (`:198`) means zero-action runs are green and unalerted.
- **W2** — state/outcome-log persistence is all-`||`-masked with no retry or conflict strategy (`x_automater.yml:161-163`), unlike the other three workflows.

**Non-blockers**
- **W3** `linkedin_engagement.yml:88` does not commit tracker-written `trial_metrics.json`/`post_history.json`.
- **W4** `linkedin_automater.yml:96` omits `data/linkedin_outcomes.json` it writes.
- **W5** `bluesky_engagement.yml:81,94-95` push failure only warns.
- **W6** no failure alert in either engagement workflow.
- **W7** "Every 6 Hours" label vs `30 */3` cron in `linkedin_engagement.yml`.
- **W8** inconsistent `GEMINI_MODEL` across workflows (validity unverifiable).
- **W9** `eval` of `inputs.topic` in `linkedin_automater.yml:83-89`.
- **W10** `data/x_followers.json` absent despite snapshot step + persist reference.

**Verified OK (no finding):** `MAX_DAILY_TOTAL=0` correctly disables the global cap in engagement workflows; all workflow cap/cooldown values map to real `config.py`/`safety.py` knobs; all dispatch `action` values are valid CLI choices; concurrency groups are coherent (`omnichannel-state-sync` intentionally shared by the two state-writing jobs); permissions are minimal and sufficient; `[skip ci]` plus no `push` trigger prevent self-trigger loops; dry-run propagates on both scheduled and dispatched runs.

**Verdict: FIX FIRST.** Fix W1 and W2 before closing the project; W3–W5 should be fixed in the same pass because they compound the state-loss/observability problem. Cross-reference `research/final-cloud-evidence.md` for the independent content/gate blockers — those remain open.
