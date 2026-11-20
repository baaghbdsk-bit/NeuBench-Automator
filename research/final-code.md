# Final validation — CODE AND QUALITY GATES

**Agent angle:** code + quality gates (syntax, tests, gate wiring, brand/URL hygiene, git state).
**Verdict: FIX FIRST**

I did not modify production code. All python snippets were run from a temp dir with
`PYTHONPATH=.` and `GEMINI_API_KEY=test-key`. One temporary `browser_session/cookies.json`
was created only to prove the test-failure root cause and was deleted afterwards
(verified absent). Git CLI is **not installed** on this machine, so git state was read
directly from `.git` (refs, logs, index) with a Python index parser and loose-object reader.

---

## 1. CONFIRMED blockers

### B1 — Test suite is RED in a clean checkout (`tests/test_x_guards.py:117-148`)

- Command: `python -m pytest -q tests` → **1 failed, 102 passed** (27s).
- Failing test: `XGuardTests::test_missing_confirmation_is_unknown_not_success`,
  `self.assertTrue(client.last_outcome_unknown)` fails at `tests/test_x_guards.py:148`.
- Root cause (verified, not a hypothesis): `src/twitter_client.py:139` branches on
  `config.COOKIES_FILE.exists()` (`config.py:8` → `browser_session/cookies.json`).
  On this checkout that file does **not** exist, so `_get_context_and_browser()`
  (`twitter_client.py:130-154`) takes the `launch_persistent_context` branch and
  returns an unconfigured `MagicMock` page. The test's mocks for
  `browser.new_context` are never used — instrumented run showed
  `page.locator` called **0** times. `post_btn.is_disabled()` then returns a truthy
  `MagicMock`, the "disabled" branch at `twitter_client.py:236-245` fires, and the
  method returns `failed` instead of `unknown`.
- Proof: with an empty `browser_session/cookies.json` present the **same** command
  yields **103 passed** (all green) — the only difference is the file's existence.
- Impact: any fresh CI runner / fresh clone (no cookies file) runs a red suite. A
  red gate cannot be signed off. Also, this test is the regression test for the
  duplicate-post safety outcome (`unknown` blocks retry via `reserve_original`),
  so its failure means that guard is untested in CI.
- Smallest fix (test-only): inject the mocked context directly, e.g. patch
  `client._get_context_and_browser` to return `(context, browser)`, or patch
  `config.COOKIES_FILE` to a temporary existing file in the test. No production
  change required.

### B2 — Release-critical fixes are UNCOMMITTED; HEAD == origin/main without them

- `.git/refs/heads/main` = `24f8fd8198cba1fc79877b618570e4d1e867fd35`
  (HEAD commit: `fix(bluesky): make generator produce the voice the quality gate requires`).
- `.git/refs/remotes/origin/main` = `24f8fd8198...`; `FETCH_HEAD` = `24f8fd8198...`.
  So **HEAD is in sync with origin/main** — but the working tree is not.
- Parsed index (527 entries, CRLF-normalized blob hashes) shows **4 modified tracked files**:
  - `src/scheduler.py` — adds `if self.safety.dry_run: return` to `_record_x_outcome`
    (`:1733`), `_record_bluesky_outcome` (`:1757`) and `_record_linkedin_outcome`
    (`:1787`). Without it, dry runs write fake outcome rows into cloud state.
  - `.github/workflows/x_automater.yml` — removes `continue-on-error: true` from the
    broadcast step and replaces the fire-and-forget push with a 3-attempt retry that
    hard-fails if the state push never succeeds.
  - `.github/workflows/linkedin_automater.yml` — replaces unsafe
    `eval "python main.py $CMD_ARGS"` with direct quoted invocations, and persists
    `data/linkedin_outcomes.json`.
  - `tests/test_x_trend_integration.py` — adds `test_dry_run_never_writes_outcome_log`.
- Impact: if the owner "closes the project" against origin/main, none of these ship —
  CI still has `continue-on-error: true`, the `eval` command construction, and the
  dry-run state pollution. The gates I verified below exist **only in the working tree**.
- Smallest fix: commit these four files before closing (and push). No code change needed.

### B3 — X and Bluesky *custom/original* publish paths bypass every gate

- `src/scheduler.py:363-424` `execute_x_custom_post()` publishes at `:407`
  `self.twitter.post_tweet(text, ...)`. Only `prepare_x_text()` (`:368`) runs — that
  function (`src/x_state.py:31-38`) merely truncates to 275 chars; it does **not**
  sanitize or gate. No `evidence_gate`, no `voice_quality_score`, no
  `sanitize_publish_text`.
- `src/scheduler.py:614-663` `execute_bluesky_custom_post()` publishes at `:657`
  `self.bluesky.post(text)` with no gate and no sanitizer at all.
- Both are reachable from the dashboard (`src/web/app.py:474`, `:669`) and the CLI
  (`main.py:167`, `:221`), so this is not dead code.
- Contrast with the autopilot originals, which are correctly gated:
  `src/scheduler.py:1453-1460` `_publish_gate(..., source_context=..., require_voice=True)`
  before `:1493 post_tweet`; `src/scheduler.py:1604-1611` same before `:1653 bluesky.post`.
- Impact: a brand name, outbound URL, unsourced number or weak-voice text entered in
  the dashboard/CLI ships verbatim. This violates the "every X original / Bluesky
  original publish path" requirement and the "no brand/URL in publish-facing strings"
  invariant (the autopilot guarantee does not extend to these paths).
- Smallest fix: in both methods, replace the raw text with
  `text = self._publish_gate(text, action_type=..., target=..., start_time=..., source_context="", require_voice=True)`,
  aborting when result is `None` — mirroring `_execute_original_post`/`_execute_bluesky_post`.

---

## 2. CONFIRMED non-blockers

### N1 — `_fix_line_starts` deletes the space after a period (`src/growth.py:76-80`)

- The replacement is `lambda m: m.group(1).upper()`, which drops the `\s+` matched
  by `r"(?<=[.!?])\s+([a-z])"`. Verified directly:
  `sanitize_publish_text("I stopped trusting p99. NeuBench telemetry shows the real gap.")`
  → `"I stopped trusting p99.Telemetry shows the real gap."` (joined `p99.Telemetry`).
- Impact: cosmetic grammar defect in publish-facing text whenever a brand mention
  followed a sentence-ending period — the exact case the "fix" was meant to repair.
  Prior research (`research/xbsky-evidence.md:101`) claimed this was fixed; it is not.
- Smallest fix: replacement `lambda m: " " + m.group(1).upper()`.

### N2 — Untracked scratch artifacts present but correctly ignored

- `generated_visuals/linkedin/test_flow/test_flow.gif` and `test_flow_first_frame.png`
  exist untracked. `.gitignore:19` (`*.png`) and `:57` (`generated_visuals/`) exclude
  them, so they will **not** be committed. No scratch/debug files are in the 527-entry
  index (the only "suspicious" names were legitimate `scripts/test_*.py` and HTML
  templates). Safe, but worth deleting for cleanliness.
- Untracked `agents/final-validation.md`, `research/final-cloud-evidence.md`,
  `research/final-workflows.md` are agent deliverables, not scratch.

### N3 — Documentation drift

- Research docs cite stale line numbers (`scheduler.py:2007`, `:452`, `:1514`, etc.).
  Current code has the gates at `:2094`, `:2241`, `:2278`, `:1453`, `:1604`. Docs are
  misleading about exact call sites; the code itself is wired correctly for the
  autopilot paths. Not a code defect.

### N4 — Stale packed-ref (informational)

- `.git/packed-refs` still has `origin/main = 055de3047...` from the original clone;
  the loose ref `.git/refs/remotes/origin/main = 24f8fd81...` overrides it. Harmless;
  a future `git pack-refs --prune` will clean it.

---

## 3. Verified clean (with evidence)

- **Syntax:** `python -m compileall -q src tests main.py config.py scripts` → exit 0.
- **YAML:** both modified workflows parse with `yaml.safe_load`.
- **Gate implementations** (`src/growth.py`):
  - `sanitize_publish_text` (`:40-61`) strips `_URL_RE` (`:14`), `_BARE_BRAND_URL_RE`
    (`:15-18`) and `_BRAND_RE` (`:13`). Direct call confirmed:
    `NeuBench telemetry ... https://example.com/post` → `Telemetry ... Read more`;
    `app.neubench.workers.dev/demo?ref=x` → `""`.
  - `voice_quality_score` (`:323-357`) is invoked **only** when `evidence_gate` gets
    `require_voice=True` (`:387-390`). Verified flag wiring:
    - LinkedIn `_execute_linkedin_post` — `evidence_gate` at `:2094-2099` and
      `:2241-2246`, both `require_voice=True` → voice check runs.
    - X original autopilot — `_publish_gate` at `:1453-1460`, `require_voice=True`.
    - Bluesky original autopilot — `_publish_gate` at `:1604-1611`, `require_voice=True`.
    - `_publish_gate` (`:1701-1731`) passes `require_question=False` (correct for X/BSky
      short form) and forwards `require_voice` (`:1717`).
  - `first_comment_gate` (`:394-408`) rejects empty, >350 chars, a second `?`, links
    and unsourced numbers. Applied in LinkedIn flow at `scheduler.py:2278` (only when
    a `carousel_plan` exists; custom-text posts have no generated first comment, so
    `first_comm=None` at `:2275` — acceptable).
  - `evidence_gate` calls `sanitize_publish_text` internally (`:373`), so every gated
    publish path returns sanitized text.
- **Brand/URL grep of `src/`** (case-insensitive, `neubench|neu[ -_]?bench|workers.dev|vercel.app`)
  → 19 matches, all accounted for: sanitizer regex (`growth.py:16`), backwards-compat
  internal aliases (`ai_generator.py:296`, `trend_hunter.py:1069`, `web/app.py:564,612`),
  and dashboard DOM ids / JS variable names (`templates/dashboard.html`). No brand
  string or brand URL is present in a literal publish-facing message.
- **Git:** `git status` equivalent — 4 modified tracked files (listed in B2), no
  staged changes detectable beyond index, no committed scratch files. HEAD == origin/main.

---

## 4. Could not verify (no credentials / no live environment)

- No git executable — git state reconstructed from `.git` internals; commit contents
  read from loose objects, not from `git diff`. Verification is byte-level and should
  be reproduced with real `git status` / `git diff` before sign-off.
- No live browser, no Gemini/X/Bluesky/LinkedIn credentials, no GitHub Actions logs.
  I could not confirm that generated drafts actually pass the voice gate in
  production, that the CI push-retry fix works, or that cloud-written state is clean.
- The 103-pass run required a synthetic `cookies.json`; I could not verify the test
  passes on the owner's real CI image without one.
- Other subagents' reports (`research/final-cloud-evidence.md`, `final-workflows.md`)
  were being written concurrently; I did not cross-validate their claims.

---

## 5. Smallest path to SHIP

1. Fix `tests/test_x_guards.py::test_missing_confirmation_is_unknown_not_success` so it
   does not depend on `browser_session/cookies.json` (B1).
2. Commit and push the 4 modified files (B2).
3. Route `execute_x_custom_post` and `execute_bluesky_custom_post` through
   `_publish_gate(..., require_voice=True)` (B3).
4. Optional cleanup: fix the dropped space in `_fix_line_starts` (N1) and delete the
   ignored `generated_visuals/linkedin/test_flow/` artifacts (N2).

**Verdict: FIX FIRST.**
