# X / Bluesky Evidence-Integrity Audit (forensic)

**Role:** cross-platform evidence auditor (same role as the LinkedIn audit that found 9/25 posts with invented statistics).
**Scope:** 𝕏 and Bluesky only. Do not modify production code.
**Evidence base:** `trial_metrics.json` → `recent_events` (500 events; `trial_meta.last_updated = 2026-11-19T20:01:54.425550+00:00`), current `src/ai_generator.py`, `src/trend_hunter.py`, `src/growth.py`, `src/scheduler.py`.
**Method (verbatim discipline):** parsed JSON with Python 3.12 `json.load` under UTF-8 (not PowerShell, which renders `’` as `â€™`). Every quote below is copied exactly as stored, including truncation. `content_preview` is cut at 120 chars (`src/x_state.py:188`, `:227`), so `[cut@120]` marks a stored truncation, not my paraphrase. Counts are stated as exact integers, never as "many". Numeric-claim detection uses the real `extract_numeric_claims()` / `evidence_gate()` from `src/growth.py`, executed directly.

**Two caveats that materially affect line numbers:**
1. **`src/scheduler.py` was being edited concurrently by another agent while I audited.** It grew from 108,554 bytes (08:00-ish snapshot) to 114,568 bytes at `2026-11-20T02:36:19+05:30`. Section 4 records both the state at spawn and the state at my final snapshot; absolute line numbers for `scheduler.py` will drift, so function names are the durable anchor.
2. No `git` executable exists on this machine (`.git` exists but cannot be queried), so I cannot show diffs. The HEAD reflog shows the growth/engagement-gate commits landed `2026-11-20T00:44–02:17+05:30` — i.e. **after every defect quoted below** (all dated `2026-11-14` … `2026-11-18`). That chronology is the basis for the "fixed vs remaining" split in §3.

---

## 1. Verbatim defects (exact strings + timestamps)

Event-type inventory (exact): `bluesky_post` 130, `original_post` 176, `linkedin_post` 141, `reply` 39, `quote_tweet` 12, `repost` 1, `bluesky-replies` 1. The X/Bluesky subset audited is 359 events.

### 1.1 Pseudo-authority + brand remnant — 4 Bluesky posts, all `status: success`

| # | Timestamp (UTC) | Verbatim `content_preview` |
|---|---|---|
| 1 | `2026-11-15T02:02:13.110302+00:00` | `Frontier LLM API degradation isn't binary. NeuBench telemetry shows micro-failures—tail-latency spikes and silent token ` [cut@120] |
| 2 | `2026-11-15T07:02:09.010440+00:00` | `NeuBench speed testing reveals up to 40% variance in real-world token throughput across major hosted LLM APIs. Don't let` [cut@120] |
| 3 | `2026-11-15T21:02:11.130577+00:00` | `NeuBench telemetry on 260+ models shows stark trade-offs in reasoning drift and token economics for long-horizon coding.` |
| 4 | `2026-11-18T05:02:03.464354+00:00` | `Frontier LLM API degradation isn't just about hard 500s; it's tail-latency spikes and silent token-drop rates. NeuBench ` [cut@120] |

These combine three defect classes in 4 shipped posts: **brand remnant** (`NeuBench`, 4/4), **pseudo-authority** (`telemetry shows`, `speed testing reveals`, `telemetry on … models`, 3/4), and **fake credential** (`on 260+ models`, 1/4 — the closest in the data to the charter's example `I spent 40 hours benchmarking 260 models`, which does **not** appear verbatim).

### 1.2 Other invented stats in shipped Bluesky posts — 6 distinct strings, all `status: success`

| Timestamp (UTC) | Verbatim `content_preview` | Detected by current `extract_numeric_claims()`? |
|---|---|---|
| `2026-11-16T04:02:18.642288+00:00` | `Most agent benchmarks only score static outputs. GH-AWTrace changes that by capturing 25k+ verified runtime execution lo` [cut@120] | **No** — `logs` is not a unit |
| `2026-11-17T04:02:03.723032+00:00` | `A $1B valuation in 90 days for an AI security startup highlights the massive demand for automated remediation. But veloc` [cut@120] | Partial — flags `$1B`, misses `90 days` |
| `2026-11-17T10:03:08.600829+00:00` | `Sage S1.5 Flash: 320B MoE routing through dedicated molecular graph and bio-sequence encoders. Solving scientific multi-` [cut@120] | Yes (`320B`) |
| `2026-11-17T15:10:14.502745+00:00` | `Zuse brings decision models—LoRA + pointer heads predicting fixed-set probabilities—to European languages across 4B, 9B,` [cut@120] | Yes (`4B`, `9B`) |
| `2026-11-18T02:02:29.582125+00:00` | `AI summaries eating 40% of search traffic shifts the web economics model. Zero-click answers reduce publisher incentives` [cut@120] | Yes (`40%`) |
| `2026-11-18T11:02:12.569708+00:00` | `Energy-Based Reasoners hit 385x inference efficiency by optimizing scalar energy minimization over autoregressive token ` [cut@120] | **No** — ASCII `x` is not matched (only `×` and `times`) |

`25k+`, `260+ models`, and `385x` are the three invented stats that the current gate's regex cannot see at all (verified by executing `extract_numeric_claims()` on the exact strings).

### 1.3 Fake credential in X original drafts — 4 instances, **all `status: failed`** (never published)

Verbatim (identical in all four): `Me explaining to my landlord that I can’t pay rent this month because my AI coding agent went on a 260-model bender and ` [cut@120]

Timestamps: `2026-11-15T13:01:46.711540+00:00`, `2026-11-15T18:01:50.212756+00:00`, `2026-11-16T12:02:05.152336+00:00`, `2026-11-17T03:01:45.025630+00:00`. Reason for all four: `BrowserType.launch: Executable doesn't exist at /home/runner/.cache/ms-playwright/chromium_headless_shell-1255/...`. **These are drafts, not shipped posts** — do not report them as published. `260-model` is also invisible to the numeric regex (`model` is not a unit).

### 1.4 Counts that constrain the claims

- X `original_post`: **21 of 176** previews contain a numeric claim per `extract_numeric_claims()`. Of those 21, 4 are the `260-model bender` fake credential (§1.3); the remaining 17 are rhetorical first-person hyperbole (`6 hours`, `$50`, `10 minutes`, `1M tokens`, `40 minutes`, `45 minutes`, `35% tax`). Those are voice, not fake telemetry — but they **are** unsourced numbers that `evidence_gate()` will reject (see §3.4).
- X `reply` (39), `quote_tweet` (12), `repost` (1), Bluesky `bluesky-replies` (1): **0** numeric claims found in previews. (Lower bound only — previews are 120-char truncations.)
- Outbound links in post bodies: **0**. The only two "http" hits are protocol names, not links: `HTTP/1.1 text pipelines, HTTP/2 binary multiplexing, HTTP/3 QUIC streaming. …` (`2026-11-16T20:01:59.759845+00:00`) and `HTTP 200 with silent API contract drops breaks LLM agents. …` (`2026-11-17T20:02:11.913393+00:00`).
- Exact phrase `I spent 40 hours benchmarking 260 models`: **0** verbatim occurrences in `trial_metrics.json`. Stated explicitly to avoid overclaiming.
- Broken grammar shipped: 1 confirmed class — the sanitizer leaves a lowercase word after a period when a mid-sentence brand is removed (§3.2). The stored previews themselves contain no other clearly broken grammar attributable to the generator.

---

## 2. Root causes in the CURRENT code

### 2.1 Prompts actively invite numbers without any sourcing rule

- `src/ai_generator.py:9-19` — `X_UNHINGED_SYSTEM_PROMPT`, line 14: `SPECIFICITY: Every post needs one concrete detail: a number, a tool, a model name, a price, or a real scenario. No vague industry commentary.` There is **no** "never invent numbers" in this system prompt. It is the system prompt for `generate_hot_take` (`:210`), `generate_sniper_reply` (`:230`), `generate_quote_tweet_commentary` (`:245`), `generate_debate_comprehension` (`:1136`) and `generate_audience_reply` (`:1157`).
- `src/ai_generator.py:194-211` — `generate_hot_take`, line 203: `Lead with the sharpest specific claim, number, or contradiction. No warm-up sentence.` This is the generator used by the X original-post path (`src/scheduler.py:1394`). Contrast `generate_ai_take` at `src/ai_generator.py:286`: `Include one specific detail from the context. Never invent numbers.` — **that safeguard is absent from the hot-take path** and `generate_ai_take` is not called by the autonomous X original flow.
- `src/ai_generator.py:298-317` — `generate_bluesky_take`, line 310: `Add one concrete engineering consequence: latency, cost, memory, reliability, or evaluation quality.` This is the direct instruction behind `NeuBench speed testing reveals up to 40% variance in real-world token throughput…`. No sourcing rule. Line 311 permits `a short question or a testable claim`, which is why `require_question=False` matters (§4.2).
- `src/ai_generator.py:32-37` — `BLUESKY_SYSTEM_PROMPT` line 35: `Values: Real-world latency, inference economics, memory hierarchies, reproducibility, and transparent evaluations.` This "we have telemetry" framing is the natural source of `NeuBench telemetry shows …` and `NeuBench telemetry on 260+ models …`.
- `generate_sniper_reply` (`:217-231`), `generate_quote_tweet_commentary` (`:233-246`), `generate_bluesky_sniper_reply` (`:319-333`), `generate_bluesky_concept_post` (`:384-406`) contain **no** number, brand, or sourcing instruction at all. Brand suppression for these comes only from the downstream sanitizer.

### 2.2 Hard-coded fallback "source" data itself contains an invented stat

`src/trend_hunter.py:1021-1066` `get_engineering_briefs()` — the fallback bank whose items become `selected_trend["summary"]` and are passed as `source_context` to the gate. Line 1038 verbatim:

> `"summary": "Token throughput varies up to 40% across hosted provider endpoints running the same model weights.",`

This is the literal upstream source of the shipped `up to 40% variance` line (§1.1 #2). It is a **fabricated engineering brief presented as a source**, so `validate_no_number_without_source()` cannot flag it: the number is "sourced" from itself.

The same bank and the educational-concept bank in `src/trend_hunter.py:1335-1833` contain many other unattributed figures used as `summary`/`golden_rule` context, e.g. `:1335` `FlashAttention reorganizes GPU memory access to make attention 3x faster`, `:1350` `reducing memory by up to 75%`, `:1365` `slashing trainable parameters by 99%`, `:1400` `reduce KV cache size by 8x`, `:1601` `gRPC binary payloads are up to 7x smaller and 10x faster`, `:1626` `100x easier to maintain`, `:1726` `microservices create 10x more latency`. These are plausible technical claims but unsourced, and they seed both X and Bluesky generation.

### 2.3 The gate's numeric regex has three blind spots that match the actual defects

`src/growth.py:162-172` `_NUMERIC_CLAIM_RE` includes `×` (Unicode) and `times?` but **not ASCII `x`**; its unit list includes tokens/cycles/bits/bytes/writes/reads but **not `models`, `logs`, or `days`**. Executed results:

| Exact string | `extract_numeric_claims()` | `evidence_gate(..., source_context="", require_question=False)` |
|---|---|---|
| `NeuBench telemetry on 260+ models shows …` | `[]` | `True, []` — **passes** |
| `Energy-Based Reasoners hit 385x inference efficiency …` | `[]` | `True, []` — **passes** |
| `GH-AWTrace … capturing 25k+ verified runtime execution logs.` | `[]` | `True, []` — **passes** |
| `FlashAttention makes attention 3x faster …` | `[]` | `True, []` — **passes** |
| `NeuBench speed testing reveals up to 40% variance …` | `['40%']` | `False, ['unsourced number: 40%']` |
| `A $1B valuation in 90 days …` | `['1B']` | `False, ['unsourced number: 1B']` |

So wiring the existing gate as-is is **necessary but not sufficient**: it would still ship `260+ models`, `385x`, and `25k+ logs` — three of the defect strings actually found.

---

## 3. Fixed vs remaining

| Defect class | Historical evidence | Status in current code | Verified how |
|---|---|---|---|
| Brand remnant `NeuBench` (4 shipped Bluesky posts) | §1.1 | **Fixed at publish** by `sanitize_publish_text()` (`src/growth.py:46-49`) — `_BRAND_RE` removes `neu\s*[-_]?\s*bench`; all X/Bluesky paths sanitize/gate before `post()`. | Direct call: `NeuBench telemetry on 260+ models…` → `Telemetry on 260+ models…` |
| Outbound links in bodies | 0 found | Already prevented: `_URL_RE` / `_BARE_BRAND_URL_RE` in `sanitize_publish_text()`. | n/a |
| Grammar after brand removal | latent | **Remaining / introduced**: `_fix_line_starts()` (`:64-78`) only capitalizes line starts, not sentence starts. `Frontier LLM API degradation isn't binary. NeuBench telemetry shows…` sanitizes to `Frontier LLM API degradation isn't binary. telemetry shows…` — lowercase `telemetry` after a period. | Direct `sanitize_publish_text()` call |
| Fake credential `260+ models`, `260-model bender` | §1.1 #3, §1.3 | **Remaining even with gate**: `models` is not a unit in `_NUMERIC_CLAIM_RE`. | Gate probe above |
| `385x` / `3x` invented multiples | §1.2 | **Remaining even with gate**: ASCII `x` not matched. | Gate probe above |
| `25k+ … logs` invented stat | §1.2 | **Remaining even with gate**: `logs` not a unit. | Gate probe above |
| `40%` variance | §1.1 #2 | **Conditionally fixed**: blocked only when `source_context` is empty; **passes** when `source_context` is the curated brief at `src/trend_hunter.py:1038`, which itself contains `up to 40%`. X original and Bluesky post paths pass `source_context=selected_trend["summary"]` (§4.3), so this defect would still ship whenever that fallback is selected. | Gate probe with both empty and brief-derived source |
| Prompt-level invitation to invent numbers | §2.1 | **Remaining**: no "never invent numbers" in `X_UNHINGED_SYSTEM_PROMPT`, `generate_hot_take`, `generate_bluesky_take`, or the reply/commentary prompts. | Current file read |
| 17 rhetorical numeric X posts (`6 hours`, `$50`, `1M tokens`, …) | §1.4 | **Regression risk**: with the gate wired and no `source_context` on reply/quote paths, these unsourcedvoice numbers are rejected, while the prompt still demands a number. Expect elevated `skipped` counts on X originals whose trend summary lacks the figure. | §4.3 + `validate_no_number_without_source()` |

Net: the sanitizer fixes the cosmetic brand class; it does not fix invented evidence. The gate fixes the `%`/`$B` class; it does not fix `models`/`x`/`logs`, and it is neutralized by fabricated source context.

---

## 4. Exact call sites for `evidence_gate()` (and `require_question` policy)

### 4.1 State at spawn (the state described in the manager brief)

Seven X/Bluesky sites called **only** `sanitize_publish_text()`; `evidence_gate()` was imported at `src/scheduler.py:82` and used only in the LinkedIn flow (`:1913`, `:2059`):

| Platform / action | Function | Original line | Original statement |
|---|---|---|---|
| X reply | `execute_x_reply` | 454 | `reply_text = sanitize_publish_text(self.ai.generate_sniper_reply("tweet_author", …))` |
| X quote | `execute_x_quote` | 537 | `quote_text = sanitize_publish_text(self.ai.generate_quote_tweet_commentary("tweet_author", …))` |
| X sniper reply | `_execute_sniper_reply` | 913 | `reply_content = sanitize_publish_text(self.ai.generate_sniper_reply(target_account, tweet_text))` |
| X quote-tweet | `_execute_quote_tweet` | 1043 | `commentary = sanitize_publish_text(self.ai.generate_quote_tweet_commentary(target_account, tweet_text))` |
| X original | `_execute_original_post` | 1379 | `hot_take = sanitize_publish_text(hot_take)` |
| Bluesky original | `_execute_bluesky_post` | 1516 | `bsky_take = sanitize_publish_text(bsky_take)` |
| Bluesky reply | `_execute_bluesky_sniper_replies` | 2492 | `reply_take = sanitize_publish_text(self.ai.generate_bluesky_sniper_reply(author, text))` |

### 4.2 Current state at my final snapshot (`2026-11-20T02:36:30+05:30`) — concurrent agent already wired the gate

A helper `Scheduler._publish_gate()` now exists at `src/scheduler.py:1670` (definition header; body ~`:1675-1693`). Its core:

```python
ok, cleaned, issues = evidence_gate(
    text,
    topic_title=target or "",
    source_context=source_context,
    require_question=False,          # line 1684
)
```

It returns `cleaned` on success; on failure it logs `↩️ {action_type} blocked by evidence gate: …` and records a `skipped` event, then returns `None`. All seven sites now call it (snapshot line numbers, **subject to drift**):

| Platform / action | Function | Line at snapshot | Passes `source_context`? |
|---|---|---|---|
| X reply | `execute_x_reply` | 454 | **No** → defaults `""` |
| X quote | `execute_x_quote` | 542 | **No** → `""` |
| X sniper reply | `_execute_sniper_reply` | 923 | **No** → `""` |
| X quote-tweet | `_execute_quote_tweet` | 1058 | **No** → `""` |
| X original | `_execute_original_post` | 1424 | Yes — `str(selected_trend.get("summary") or "")` |
| Bluesky original | `_execute_bluesky_post` | 1574 | Yes — `str(selected_trend.get("summary") or "")` |
| Bluesky reply | `_execute_bluesky_sniper_replies` | 2640 | **No** → `""` |

**Correct call-site policy — gate immediately after generation, before `reserve_target()`/`reserve_original()`/`_reserve_platform()` and before `post_tweet()`/`post_reply()`/`bluesky.post()`/`bluesky.reply()`.** The current placement satisfies that.

### 4.3 Is `require_question=False` needed? **Yes — for all four categories.**

`evidence_gate()` defaults `require_question=True` (`src/growth.py:299`), which runs `validate_one_question()` (`:275-291`): zero `?` ⇒ `"no closing question"`. The current generators do not produce questions by design:

- X originals: `generate_hot_take` (`src/ai_generator.py:194-211`) says `Lead with the sharpest specific claim, number, or contradiction… The reader should want to reply or quote it` — no question required.
- X replies / quotes: `generate_sniper_reply` (`:217-231`) and `generate_quote_tweet_commentary` (`:233-246`) request a single sarcastic sentence.
- Bluesky posts: `generate_bluesky_concept_post` (`:384-406`) has no question instruction; `generate_bluesky_take` (`:298-317`) permits *either* `a short question or a testable claim`.
- Bluesky replies: `generate_bluesky_sniper_reply` (`:319-333`) requests `1-2 sentence` technical reply, no question.

With the default `True`, every legitimate X reply, X quote, Bluesky concept post and Bluesky reply would be rejected as `"no closing question"`. The concurrent helper's `require_question=False` is therefore correct. Trade-off to record: it also disables the `bait question` / `too many questions` checks, so `thoughts?`-style bait is no longer blocked.

**Second required fix at the call sites:** the five reply/quote paths pass no `source_context`, so `validate_no_number_without_source()` will reject *any* number in a reply — including numbers that appear in the target tweet. They should pass `source_context=target_text` (source: the tweet/post being replied to or quoted), otherwise the gate will suppress legitimate engagement text. `src/ai_generator.py:14` still demands a number in every X post, so this conflict will surface immediately.

---

## 5. Top 3 findings, strongest recommendation, biggest uncertainty

**Top 3 findings**
1. **Three invented-stat classes slip straight through the gate.** `260+ models`, `385x`, and `25k+ … logs` all return `extract_numeric_claims() == []` and `evidence_gate(..., "") == (True, [])` — even though all three appeared verbatim in shipped Bluesky posts. Adding `evidence_gate()` is not enough; `_NUMERIC_CLAIM_RE` (`src/growth.py:162-172`) must gain ASCII `x`, `models`, `logs`, `days`.
2. **The gate is neutralized by a fabricated "source".** `src/trend_hunter.py:1038` hard-codes `"Token throughput varies up to 40% across hosted provider endpoints…"` as a `summary`; that summary is passed as `source_context` on the X original and Bluesky original paths, so the shipped `up to 40% variance` claim is treated as sourced. The source itself must be scrubbed (or require a real URL/provenance field), not just the output.
3. **Brand remnants are fixed; the underlying pseudo-authority is not.** 4 shipped Bluesky posts used `NeuBench telemetry…` / `NeuBench speed testing…`; `sanitize_publish_text()` now strips `NeuBench`, but the resulting `Telemetry on 260+ models…` / `Speed testing reveals up to 40% variance…` still assert fake first-party measurement, and the sanitizer also introduces a lowercase-after-period grammar defect (`… isn't binary. telemetry shows…`).

**Strongest recommendation**
Wire the gate everywhere (the concurrent `_publish_gate()` already does this with the correct `require_question=False`) **and** immediately harden `_NUMERIC_CLAIM_RE` to include `\bx\b`, `models?`, `logs?`, `\bdays?\b`, plus `_fix_line_starts()` to capitalize sentence starts after `. `/`! `/`? `. In the same change, remove the invented numbers from `src/trend_hunter.py`'s curated briefs/concepts (starting at `:1038`) and pass `source_context=target_text` on the five reply/quote call sites. Rank by impact × ease: all four are small, local edits that close the exact defects observed; regenerating prompts alone is lower value because the prompt rewrites still contain no "never invent numbers" rule.

**Biggest uncertainty**
`content_preview` is truncated to 120 characters, so I cannot see the full shipped text: the `260-model bender` X drafts are 4/4 failed (never published), and I cannot verify what followed the `[cut@120]` marks on the six shipped Bluesky strings — a full-text audit may reveal more defects but I will not assert them. Secondary uncertainty: `src/scheduler.py` was being edited concurrently during this audit, so the §4.2 line numbers are a snapshot and may already be stale; the function names and call ordering are the durable facts.
