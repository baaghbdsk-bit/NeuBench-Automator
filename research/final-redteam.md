# Final Red Team — Public Embarrassment Risk

**Angle:** RED TEAM / EMBARRASSMENT RISK. I attacked our own signoff.
**Snapshot:** reviewed 2026-11-20 15:35–15:42 local. Production files were being
modified concurrently (mtime 15:37), so all line numbers are a snapshot; each
finding also carries an exact quote so it survives line drift.

## Verdict: FIX FIRST

There is already one live post on the owner's profile with an LLM-invented
first-person war story, and the attachment pipelines can render invented metrics
and "Save this" begging with no evidence gate. The signoff claim that generic /
fabricated copy is rejected "before the browser is opened" is not true. This is
not a "measure and iterate" problem — it is a correctness problem on a public
personal profile.

---

## BLOCKERS — CONFIRMED

### B1. A fabricated first-person anecdote is already live on the owner's LinkedIn

- **Evidence (shipped state):** `data/linkedin_outcomes.json` records
  `posted_at: "2026-11-20T06:02:19.289345+00:00"`,
  `post_urn: "urn:li:ugcPost:7529423859377197057"`. The matching success event in
  `trial_metrics.json` has
  `content_preview: "I spent a week debugging why our vector search latency spiked during peak load, and I realized we completely misunderstand..."` (stored truncation at 120 chars).
  The topic was "How Vector Database HNSW Indexing Works Under the Hood".
- **Why it is fabricated:** no stored state shows the owner ever ran a week-long
  debugging session or an "our vector search latency spiked" incident; the line
  was authored by Gemini under `src/ai_generator.py:716` — "write the first line
  in FIRST PERSON with a real consequence ... **Say what you did, what broke**, or
  what you changed your mind about." The prompt bans invented *numbers* at `:718`
  but never bans invented *personal experience*. `_BANNED_OPENERS_RE`
  (`src/growth.py:181-187`) does not include "I spent". The voice rubric actively
  rewards it: `src/growth.py:331-332` gives `pov = 2` for any head starting with
  "I", and `:389` only rejects `score < 7 / pov < 1 / specificity < 1`.
- **Impact:** a real reader sees the owner claiming a week of debugging work that
  did not happen. This is the exact failure mode the voice rule was supposed to
  prevent, and it shipped *through* the voice gate.
- **Smallest fix:** add an unsourced-personal-episode check to `evidence_gate`
  (reject `I spent \d+ (hour|day|week|month)|our .* (spiked|broke|failed)` unless
  the clause is in `source_context`), add the shipped 120-char preview as a
  regression test, and change `ai_generator.py:716` to require stance without
  inventing an episode ("I would not default to X" is fine; "I spent a week" is not).
  Delete or correct the live post — no code change fixes what is already published.

### B2. Visual specs render fabricated metrics and absolutes; no gate touches them

- **Evidence:** `src/ai_generator.py:875` `"< 120 nanoseconds"`, `:899`
  `"900 GB/s via NVLink fabric"`, `:865` `"guaranteed zero false negatives"`,
  `:877` `"Bounded strictly at 1.0%"`, `:925` `"Exactly-once via log sequence"`,
  `:973` `"Sub-millisecond guarantees"` — all in
  `_build_deterministic_architecture_spec()` (`:835`), returned at `:833` when
  Gemini fails. Even the *LLM* spec prompt (`:790-ish`) instructs: "METRICS ...
  Real-world engineering benchmarks ... with concrete units" with no
  "never invent a number" rule, so the happy path can fabricate too.
- **No gate on the visual:** `evidence_gate()` is called only three times in
  `src/scheduler.py` — `:1733` (X/Bluesky), `:2121` (LinkedIn draft text),
  `:2268` (LinkedIn final text). `carousel_plan = sanitize_plan(plan)` at `:2150`
  is brand/URL cleaning only; it is rendered at `:2199`. `arch_spec` is built at
  `:2219` and rendered at `:2226`; `spec=arch_spec` at `:2257` reaches
  `validate_visual_integrity()` which checks only file size and generic component
  names (`linkedin_portfolio_manager.py:176-201`). The fabricated metric strings
  are detectable — `extract_numeric_claims("900 GB/s via NVLink fabric and < 120 nanoseconds")`
  returns `['900 GB/s', '120 nanoseconds']` — but nothing calls the gate on them.
- **Impact:** slides/GIFs attached to the owner's professional profile assert
  fake benchmarks and absolute guarantees as fact. This is precisely
  `SYNTHESIS.md:43-44` Wave 0 items 2–3 ("apply the same gate ... to the visual
  spec before `render_editorial_architecture_gif()`"; "delete ... fake visual
  metrics at `:829-975`") — still unimplemented.
- **Smallest fix:** before `render_linkedin_carousel()` / `render_editorial_architecture_gif()`,
  run `evidence_gate()` over every string in `cover/slides/pages/metrics/steps` with
  `source_context=topic_summary`; on failure suppress the visual and post
  text-only. Make the deterministic fallback qualitative-only (no `val` with
  units), and add the "never invent a number" sentence to the spec prompt.

### B3. Every flow visual begs for saves, baked into the pixels

- **Evidence:** `src/linkedin_diagrams.py:563`
  `subtitle_text = f"{subtitle} · Save this." if subtitle else "Save this."`
  and `:745` `draw.text(..., "Save this", ...)`. The static PNG carrying this text
  is the **default** attachment (`scheduler.py` flow branch; `LINKEDIN_PREFER_STATIC_VISUALS`
  defaults to `"true"`). `SYNTHESIS.md:63` said "Remove 'Save this' begging and emoji
  decoration from visuals" — not done.
- **Impact:** engagement-begging text on a professional profile attachment;
  cheapens the owner's brand and directly contradicts our own written policy.
- **Smallest fix:** delete both strings, keep a neutral footer + page number; add
  an attachment text check that rejects "Save this" before `automater.post()`.

### B4. The voice rubric is keyword theater and our docs claim it is not

- **Evidence:** executed against the current `src/growth.py`:
  a generic, content-free draft ("I think most teams get this wrong when they tune
  latency and memory in a kv cache ... Latency is the cost. Memory is the
  trade-off ... Most teams do not measure the boundary") scores
  `(10, {'pov': 2, 'stakes': 2, 'stance': 2, 'specificity': 2, 'clean_open': 2})`
  and `evidence_gate(..., require_voice=True)` returns `(True, [], [])`.
  Mechanically: `src/growth.py:331-332` grants full POV for an "I" prefix; `:338-339`
  counts isolated stake words; `:341-343` accepts any of "most teams"/"beats"
  anywhere; `:345-349` accepts any two technical nouns; `:353` sums to 10.
- **Docs contradicted:** `GROWTH_PLAYBOOK.md:74-78` — "Generic explainers and
  fabricated metrics are rejected before the browser is opened";
  `XBSKY_SYNTHESIS.md:53-57` — "The generic explainer that earned 3.5/10 can no
  longer ship." `tests/test_growth.py:145-163` never tests a keyword-stuffed
  generic draft; its "generic" case starts with the already-banned "What is".
- **Does the gamability matter? Yes.** The author is the same LLM that writes the
  post, so it can satisfy the keywords at zero cost. B1 is the real-world proof:
  "I spent a week..." scored full POV because it started with "I". The rubric is
  measuring surface tokens while the signoff sells it as a quality guarantee.
- **Smallest fix:** either stop claiming the rubric rejects generic explainers, or
  replace keyword counts with checks that cannot be satisfied by stuffing — e.g.
  reject "I think/I believe/most teams" as the entire POV, require a topic-specific
  concrete noun *phrase* (not a bare token), and reject unsourced personal-episode
  claims (B1). Add the 10/10 generic draft as a test that must fail.

### B5. The no-confirmation duplicate guard is failing and the test count is overstated

- **Evidence:** `python -m pytest -q` in this workspace → **88 passed, 16 failed**
  (most failures are `AIGenerator()` needing `GEMINI_API_KEY`). With a dummy
  `GEMINI_API_KEY` → **102 passed, 2 failed**. One env-independent failure is
  `tests/test_x_guards.py::XGuardTests::test_missing_confirmation_is_unknown_not_success`:
  assertion `self.assertTrue(client.last_outcome_unknown)` → `AssertionError: False is not true`.
  The observed call returns `last_outcome='failed', unknown=False, msg='X post button remained disabled.'`
- **Impact:** the scheduler uses `unknown` to block retries (`src/scheduler.py:813-815`,
  `:1013`, `:423`); when a submission is sent but not confirmed and the client
  reports definitive `failed`, the topic is not reserved as unknown and the next
  runner can publish the same tweet again. `GROWTH_PLAYBOOK.md:92-94` calls this
  failure "unrelated to the growth work" but it is the duplicate-post guard.
  `GROWTH_PLAYBOOK.md:78` claims "101 tests pass" — not reproducible locally.
- **Smallest fix:** classify the no-confirmation path in `TwitterClient.post_tweet`
  with `_finish_outcome("unknown", ...)`, make the test pass, re-run and print the
  exact count in the doc.

---

## NON-BLOCKERS — CONFIRMED

### N1. Two publish paths bypass the signoff gate entirely

- `main.py debate-sniper` → `src/scheduler.py:1253` `_execute_x_debate_sniper`:
  `reply_take = self.ai.generate_debate_comprehension(...)` at `:1273`, then
  `post_reply` at `:1277` with **no** `_publish_gate`, no reservation, no dedupe.
  That generator's own prompt (`src/ai_generator.py:1138-1153`) asks for a
  "devastatingly funny, sarcastic", "unapologetically unfiltered" take on
  "political, religious, cultural" debates.
- `main.py mentions` → `src/scheduler.py:1210-1228`: `generate_audience_reply`
  ("sharp wit, sarcasm, playful banter", `ai_generator.py:1159-1175`) posted with
  no gate.
- Neither is in `x_automater.yml` (it calls `reply`/`repost`, which *are* gated),
  so they are not on the current scheduled path. But both are live CLI actions.
  `XBSKY_SYNTHESIS.md:34` records the red-team veto of off-niche roasts as
  "Accepted"; the code still contains them. **Fix:** route through `_publish_gate`
  or remove the CLI actions.

### N2. Generated alt text is thrown away

`src/linkedin_visuals.py:851` returns `alt_text`; the `automater.post()` call in
`scheduler.py` passes only `media_title`, and `linkedin_automater.py:463` sets
`altText` to `resolved_title` (default `"Engineering Brief"`). `SYNTHESIS.md:62`
said to wire it. Accessibility/quality only.

### N3. Dashboard presents invented numbers as profile data

`src/web/app.py:258` `current_followers = 20  # Live follower base`,
`:270` `estimated_impressions = total_actions * 4500`, surfaced in the `profile`
object at `:302/:308`. A separate `metric_transparency` block (`:316-320`) admits
they are "hardcoded_constant/simulated" and "estimated" — but the headline fields
do not. `GROWTH_PLAYBOOK.md:80-81` says "no gain is claimed from estimated
numbers". If the dashboard is linked publicly, "20 followers" plus inflated
impressions are an embarrassment. **Fix:** show `null`/"not measured yet" or put
the estimate label inline.

### N4. Unauthenticated post endpoints (exposure unverified)

`src/web/app.py:962` `POST /api/action/publish-linkedin` accepts arbitrary `text`
and calls `execute_linkedin_custom_post()` → `_execute_linkedin_post(..., force=True)`
(`scheduler.py`), bypassing the daily cap and cooldown. No auth middleware found
in `app.py`. If this dashboard is only local, impact is nil; if it is the
Cloudflare deployment implied by `cloudflare_dashboard/`, anyone can publish to
the owner's LinkedIn. **Fix:** authenticate the endpoint and drop `force=True`
for web-triggered posts.

### N5. The "Executive Quality Gate" checks less than its name implies

`src/linkedin_portfolio_manager.py:122-159` still checks length and a placeholder
list only (`:143`); `pre_publish_review_and_gate()` never passes `topic_summary`
or runs the evidence/voice checks. `SYNTHESIS.md:45` Wave 0 item 4 said to harden
it. The final `evidence_gate` at `scheduler.py:2268` still protects text, so this
is defense-in-depth, not a live text hole — but console output "Running Pre-Publish
Executive Quality Gate" overstates it.

### N6. Post-fix off-niche filter has no production evidence

The code filter exists (`scheduler.py:1343` `_on_niche_x`), but the last
successful X *originals* in `trial_metrics.json` are sports/celebrity roasts
through `2026-11-19T04:15`; the only post-fix X success is `2026-11-20T07:02`,
a reply ("...vibrating at Claude until it builds a whole-ass streaming platform").
Do not claim the filter works from outcomes until an on-niche original ships.

### N7. Exact 6-hour Cron cadence

`.github/workflows/x_automater.yml:6` `cron: '0 */6 * * *'` publishes X/Bluesky at
exactly 00/06/12/18 UTC. `GROWTH_PLAYBOOK.md:22-23` documents this as intended;
low embarrassment risk, but it is a perfectly regular machine signature.

---

## CANNOT VERIFY (stated explicitly)

- **No credentials:** cannot call Gemini, LinkedIn, X or Bluesky; cannot confirm
  what any live post or attachment actually contains. All `content_preview`
  strings are cut at 120 chars (`XBSKY_SYNTHESIS.md:23`), so B1's full body is
  unfalsifiable from local state.
- **No live browser:** could not inspect any generated attachment at 320px, so
  `SYNTHESIS.md:64` ("verify every attachment at 320px") remains unverified.
- **No GitHub Actions logs:** cannot confirm any workflow ran post-release, that
  engagement workflows produce events, or that cloud state matches these local
  JSON files. `linkedin_engagement_history.json` is still `{"engagements": []}`.
- **No network exposure check:** cannot determine whether the dashboard (N4) is
  public, so its severity is unknown.
- **Concurrent edits:** other agents modified production files at 15:37 during
  this review. I re-ran every critical grep after that timestamp; all blockers
  above were still present. Line numbers are a snapshot as of 15:41.
