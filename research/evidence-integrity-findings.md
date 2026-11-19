# Evidence Integrity Findings — LinkedIn publishing pipeline

**Auditor role:** `agents/evidence-integrity-auditor.md`
**Date:** 2026-11-20
**Scope:** LinkedIn generation paths in `src/ai_generator.py`, sanitization in `src/growth.py`, the LinkedIn publish path in `src/scheduler.py`, and every `linkedin_post` preview in `trial_metrics.json`.
**Constraint honoured:** no production code was modified. This document is the deliverable.

---

## Executive summary

1. **Fabricated statistics are shipped as fact, and the pre-publish gate is blind to them.** Twenty-five successful `linkedin_post` events are in `trial_metrics.json`; at least **nine lead with an invented number**. `LinkedInPortfolioManager.validate_article_quality()` (`src/linkedin_portfolio_manager.py:122-159`) checks length, placeholder strings and visual alignment — **never facts** — so the "🛡️ Executive Pre-Publish Quality Gate" (`src/scheduler.py:1988-2005`) actively rubber-stamps them.
2. **The repeated-title grammar bug is a deterministic fallback template, not an LLM slip.** `generate_full_linkedin_article()` (`src/ai_generator.py:740-741`) hard-codes `f"Understanding the real-world mechanics of {topic}{comp_str} is one of the most critical fundamentals in modern systems design."` When `topic` is already a question like `"What is a Bloom Filter?"`, the output is the shipped line `What is a Bloom Filter?\n\nUnderstanding the real-world mechanics of What is a Bloom Filter? is one of the most critical f…`. This bypasses the model entirely on generation failure.
3. **The recent `src/growth.py` work fixed brand/URL hygiene only.** `sanitize_publish_text()` strips `neubench`, bare domains, URLs, dead labels and dangling connectors, but touches **no digit, unit, percentage, absolute claim, proper noun or repeated sentence**. Zero of the fabricated numbers below are caught.

**Single strongest recommendation:** add a hard `evidence_gate()` choke point immediately after `li_text = sanitize_publish_text(final_text)` at `src/scheduler.py:2007` that rejects any post containing a numeric claim not present verbatim (after unit normalization) in the sourced context, with **skip-on-failure** — never silent strip. One call site protects autonomous, custom-text and custom-topic LinkedIn posts.

---

## 1. Exact broken output (quoted verbatim)

All quotes are copied from `trial_metrics.json` `recent_events[].content_preview` for `action_type == "linkedin_post"`, `status == "success"`. The tracker truncates previews at ~140 chars; `[…truncated…]` marks that boundary, not a paraphrase. The short labels in the brief ("60% of GPU cycles wasted", etc.) are the canonical defect names.

### 1a. Fabricated statistics (unsourced numbers presented as fact)

| # | Exact shipped quote | Location / timestamp |
|---|---|---|
| F1 | `Your expensive A100 GPU cluster is sitting idle 60 percent of the time during LLM inference, and static batching is the […truncated…]` | `trial_metrics.json:1658`, 2026-11-16T19:38:13Z |
| F2 | `During a massive 500-billion parameter training run, up to 60 percent of expensive GPU compute cycles are routinely wast[…truncated…]` | `trial_metrics.json:2698`, 2026-11-18T00:20:02Z — **"60% of GPU cycles wasted"** |
| F3 | `Your LLM inference cluster is likely wasting 60 to 80 percent of its GPU memory on empty air. […truncated…]` | preview 2026-11-16T06:02:13Z |
| F4 | `A single paragraph of code can quietly bloat your LLM inference budget by 300 percent simply because of how a word is sp[…truncated…]` | `trial_metrics.json:3228`, 2026-11-18T11:02:05Z — **"300% budget bloat"** |
| F5 | `Your multi-threaded application passes all synthetic benchmarks, yet production p99 latency spikes by 300 percent under […truncated…]` | `trial_metrics.json:348`, 2026-11-15T05:02:32Z |
| F6 | `Your GPU is sitting idle for 5 microseconds doing absolutely nothing, and at scale, that invisible gap is quietly destro[…truncated…]` | `trial_metrics.json:4298`, 2026-11-19T06:02:43Z — **"5 microseconds idle"** |
| F7 | `Imagine searching across 10 billion web pages and getting results in under 50 milliseconds. If a search engine scanned e[…truncated…]` | preview 2026-11-15T01:26:45Z |
| F8 | `Your database can handle 100,000 writes per second, but a single unexpected query spike brings your entire application t[…truncated…]` | preview 2026-11-17T03:55:21Z |
| F9 | `Scanning 10 million documents word-by-word takes about 5 seconds. Users abandon search bars if they wait longer than 100[…truncated…]` | preview 2026-11-17T16:02:42Z |
| F10 | `Every production AI agent looks brilliant in a Jupyter notebook, but when traffic hits 10,000 concurrent sessions, state[…truncated…]` | preview 2026-11-14T22:25:23Z |

None of these numbers appear in the topic's `summary`/`context`. They are invented by the model and published unchanged.

### 1b. Repeated title text + broken grammar (deterministic template)

| # | Exact shipped quote | Location / timestamp |
|---|---|---|
| R1 | `What is a Bloom Filter?\n\nUnderstanding the real-world mechanics of What is a Bloom Filter? is one of the most critical f[…truncated…]` | `trial_metrics.json:3678`, 2026-11-18T19:02:46Z |
| R2 | `What is Context Window Poisoning? The Silent Killer of Long-Form LLM Memory\n\nUnderstanding the real-world mechanics of W[…truncated…]` | preview 2026-11-18T14:03:28Z |
| R3 | `LLM KV Cache Eviction and PagedAttention\n\nUnderstanding the real-world mechanics of LLM KV Cache Eviction and PagedAtten[…truncated…]` | preview 2026-11-19T17:03:47Z |

Defect: the title is printed twice (once as its own line, once embedded mid-sentence), and a question-form title ("What is a Bloom Filter?") is grammatically embedded as a noun phrase. The copy bug reported in the brief — `Understanding the real-world mechanics of What is a Bloom Filter? is one of the most critical…` — is R1.

### 1c. Hallucinated tool / paper / metric names in the *visual* spec (hard-coded fallbacks)

These are deterministic, in production code, and feed carousel/GIF assets (`_build_deterministic_architecture_spec`, `src/ai_generator.py:829-975`):

- `src/ai_generator.py:869-871`: `< 120 nanoseconds`, `9.6 bits per stored key`, `Bounded strictly at 1.0%` — presented as measured Bloom Filter metrics with no source.
- `src/ai_generator.py:893-895`: `900 GB/s via NVLink fabric`, `2*(N-1)/N chunks transferred`, `< 45 microseconds`.
- `src/ai_generator.py:941-943`: `~1.2 GB per 10k tokens`, `< 45ms prefill latency`, `1.8 TB/s HBM throughput`.
- `src/ai_generator.py:863`: `"Murmur3 Hashers"`, `:935`: `"FlashAttention V3"`, `:936`: `"PagedKV Ring Buffer"` — versioned/productized names that do not exist as named components; `"FlashAttention V3"` in particular is a hallucinated version.

`generate_comparison_plan()` embeds unsourced metrics directly in its prompt schema examples (`src/ai_generator.py:1460-1462`, `:1557-1561`): `"Millions msg/sec (sequential I/O)"`, `"Tens of thousands msg/sec (random I/O)"`, `"Millions/sec via sequential I/O"`. The model is being *shown* fake numbers as the expected output shape.

### 1d. Absolute claims

- `guaranteed zero false negatives` — `src/ai_generator.py:859` (Bloom filter fallback subtitle; true in theory for a standard Bloom filter but asserted without the bounded-membership caveat).
- `Bounded strictly at 1.0%` — `src/ai_generator.py:871`.
- `Sub-millisecond guarantees` — `src/ai_generator.py:967`.
- `Exactly-once via log sequence` — `src/ai_generator.py:919`.
- Preview F4's phrasing `A single paragraph of code can quietly bloat…` is hedged, but the quantified claim is not.

### 1e. Dangling brand remnants / broken formatting

**Already fixed by `src/growth.py`** (see §3). No live `neubench`, `app.neubench.workers.dev`, `neubench.vercel.app`, `https://`, bare `(  )`/`[  ]`, or `live evals:`/`benchmarks live:` remnants remain in the 25 successful LinkedIn previews. `_BRAND_RE`, `_URL_RE`, `_BARE_BRAND_URL_RE`, `_DEAD_LABEL_RE`, `_CONNECTOR_RE` and `_fix_line_starts()` in `src/growth.py:13-78` are the fix. The one residual risk is that `_BRAND_RE` also deletes brand words used as legitimate subject matter, but that is a voice issue, not an evidence issue.

---

## 2. Which prompt caused each defect

The LinkedIn publish path is `src/scheduler.py:_execute_linkedin_post()` (`:1597-2096`). Topic ideation → `AIGenerator.ideate_autonomous_tech_topic()` (`:1613`); format pick → `select_linkedin_content_format()` (`:1778`); plan generation → `generate_comparison_plan()` / `generate_educational_notes_plan()` / `generate_linkedin_carousel_plan()` (`:1389` / `:1180` / `:508`); long-form expansion → `generate_full_linkedin_article()` (`:662`); then the portfolio gate and `sanitize_publish_text()`.

| Defect | Causing instruction (exact source) | Why it fails |
|---|---|---|
| F1–F10 (fabricated stats) | `generate_full_linkedin_article()`, `src/ai_generator.py:702-703`: **"Start with an eye-opening metric, striking paradox, or real-world comparison that stops the feed scroll immediately (e.g. parameter count contrast, latency gap, or hidden production bottleneck)."** This explicitly rewards inventing a metric and supplies **no source context and no "never invent numbers" rule**. | The hook is the first thing generated, and `summary` is often qualitative or empty. The model manufactures a plausible number. |
| F1–F10, continued | `generate_linkedin_take()`, `src/ai_generator.py:429`: the example hook is **"I spent 40+ hours benchmarking 260+ models on [Topic]. Here is the 1-page visual cheatsheet so you don't burn your cloud budget:"** — a fabricated credential and counts modelled as the desired output. | Few-shot by example beats a generic tone rule. |
| F4 / F6 specifically | Same as above, plus `src/ai_generator.py:756` hook pattern: "striking paradox". | n/a |
| R1–R3 (repeated title / broken grammar) | **Absence of a guard**, plus the hard-coded fallback at `src/ai_generator.py:740-741`: `f"{topic}\n\n"` and `f"Understanding the real-world mechanics of {topic}{comp_str} is one of the most critical fundamentals in modern systems design.\n\n"`. Reached when `_generate_with_fallback()` throws (all Gemini models fail) — caught at `:730-731`. | `topic` is already a full title/question, so it is duplicated and parsed as a noun phrase. `comp_str` (`:733`) can inject ` between X and Y` into the same sentence. |
| §1c hard-coded visual metrics | `_build_deterministic_architecture_spec()`, `src/ai_generator.py:829-975`, and the JSON schema examples in `generate_comparison_plan()`, `:1459-1462`, `:1557-1561`. | This is not generation at all — invented numbers are source code literals rendered into the carousel/PDF/GIF. No prompt change can fix it. |
| §1d absolute claims | `src/ai_generator.py:859`, `:871`, `:919`, `:967` (fallback strings) and the missing "no absolutes" rule in every LinkedIn system prompt. | `PROFESSIONAL_TECH_SYSTEM_PROMPT` (`:25-30`) says "grounded in real-world systems engineering" but never forbids guarantees. |
| Dangling brand remnants | Previously produced by prompts that named the brand/tracker (e.g. `:373` "The interactive benchmark tracker is mentioned for the first comment", `:411` link instruction). **Now neutralised downstream** by `sanitize_publish_text()` at `src/scheduler.py:1890`, `:2007`, `:2025`. | Fixed. |
| Gate blind spot | `LinkedInPortfolioManager.validate_article_quality()`, `src/linkedin_portfolio_manager.py:122-159`, and `validate_educational_plan()`, `src/ai_generator.py:1794-1813`. | Both validate **density and structure only**. `validate_educational_plan` returns `True` for a plan whose every page contains fabricated numbers. |

**Important contrast:** two prompts *do* already say the right thing — `generate_ai_take()` (`:286`) "Never invent numbers." and `generate_linkedin_carousel_plan()` (`:556`) "Never invent a number, date, name, quote, funding amount, or study result. If a metric is not provided, describe the risk or the action qualitatively instead." with system prompt `:571` "you never invent facts." These rules are **not propagated** to the article/plan paths that actually produced the defects, and even `generate_linkedin_carousel_plan()` calls the metric-hungry `generate_full_linkedin_article()` at its fallback (`:641-645`). Copying the `:556` sentence into every LinkedIn prompt is a cheap mitigation but **not sufficient** — it is still vibes, not enforcement.

---

## 3. Fixed by recent changes vs. still remaining

| Defect class | Status | Evidence |
|---|---|---|
| Brand names in body (`neubench`, spaced/hyphenated variants) | **FIXED** | `_BRAND_RE` `src/growth.py:13`, applied via `sanitize_publish_text()` `src/scheduler.py:1890`, `:2007`. |
| Bare brand URLs (`app.neubench.workers.dev`, `neubench.vercel.app`) and `http(s)` URLs | **FIXED** | `_URL_RE`, `_BARE_BRAND_URL_RE` `src/growth.py:14-18`. |
| Dead trailing labels after URL removal (`live evals:`, `benchmarks live:`, `compare live:`) | **FIXED** | `_DEAD_LABEL_RE` `src/growth.py:26-30`. |
| Dangling connectors (`… live`, `… using.`) and empty `()`/`[]` | **FIXED** | `_CONNECTOR_RE` `src/growth.py:19-22`, `src/growth.py:51-52`. |
| Lowercase line start after a brand token was removed | **FIXED** | `_fix_line_starts()` `src/growth.py:64-78`. |
| Near-duplicate topics recycled | **FIXED** (topic level) | `filter_fresh_topics()` / `is_near_duplicate_topic()` `src/growth.py:111-155`, called `src/scheduler.py:1772`, `:1808`, `:1832`. Note this checks **titles**, not factual content. |
| **Fabricated numbers / percentages / units (F1–F10)** | **REMAINS** | `sanitize_publish_text()` never inspects digits; no validation function exists anywhere in the pipeline. |
| **Repeated title / `Understanding the real-world mechanics of …` template (R1–R3)** | **REMAINS** | Hard-coded at `src/ai_generator.py:740-741`; `validate_article_quality()` only checks length/placeholders, and the phrase is not in its placeholder list (`:143`). |
| **Hard-coded unsourced metrics in visual fallbacks (§1c)** | **REMAINS** | `src/ai_generator.py:829-975`, `:1459-1462`, `:1557-1561` unchanged. |
| **Absolute claims / guarantees (§1d)** | **REMAINS** | No forbidden-phrase list exists. |
| **Hallucinated tool/paper names** | **REMAINS (partially masked)** | `_BRAND_RE` only removes the brand; `"FlashAttention V3"`, `"Murmur3 Hashers"`, `"PagedKV Ring Buffer"` survive. |
| Other-platform numbers (X/Bluesky previews such as `$24M seed`, `385x more efficient inference`) | **REMAINS / out of primary scope** | Same missing rule; `sanitize_publish_text()` applied at `src/scheduler.py:452`, `:535`, `:911`, `:1041`, `:1377`, `:1514` also skips numbers. |

Net: **~6 defect classes fixed, 6 remain.** The fixes are all *cosmetic/brand*; the integrity problem is untouched.

---

## 4. Deterministic pre-publish validation rules (proposed; exact names and call sites)

Implement in a new module `src/evidence_guard.py` (or append to `src/growth.py` — it belongs with the other pre-publish hygiene helpers). All functions are pure and deterministic; no LLM calls.

### 4.1 Regex constants

```python
NUMERIC_CLAIM_RE = re.compile(
    r"\b\d[\d,]*(?:\.\d+)?\s*"
    r"(?:%|percent\b|percentage\b|×|x\b|times?\b|"
    r"ms\b|milliseconds?\b|µs\b|us\b|microseconds?\b|ns\b|nanoseconds?\b|"
    r"s\b|seconds?\b|minutes?\b|hours?\b|"
    r"[KMGT]?B(?:/s)?\b|GB/s\b|TB/s\b|IOPS\b|qps\b|reqs?/s\b|"
    r"tokens?\b|cycles?\b|mW\b|dB\b|bits?\b|bytes?\b|"
    r"thousand\b|million\b|billion\b|trillion\b)",
    re.IGNORECASE,
)
ABSOLUTE_CLAIM_RE = re.compile(
    r"\b(?:always|never|every|all|100\s*%|zero|guarantee(?:d|s)?|"
    r"eliminat(?:e|es|ed|ing)|impossible|provably|definitively|"
    r"no\s+(?:errors?|exceptions?|false\s+positives?))\b",
    re.IGNORECASE,
)
REPEATED_TITLE_RE = re.compile(r"^(.{8,120}?)\s*[\n.!?]\s*\1", re.IGNORECASE | re.DOTALL)
BROKEN_TEMPLATE_RE = re.compile(
    r"Understanding the real-world mechanics of\b|"
    r"is one of the most critical fundamentals\b|"
    r"\bWhat is .{0,80}\?\s+is\b",
    re.IGNORECASE,
)
STRUCTURAL_NUMBER_ALLOWLIST_RE = re.compile(
    r"^(?:Day\s+\d+\s*/\s*\d+|Step\s+\d+|\d+[.)]\s|[A-Z][A-Za-z0-9]*-\d+)$"
)
```

### 4.2 Functions and exact call sites

| Function | Signature / behaviour | On failure | Call site |
|---|---|---|---|
| `extract_numeric_claims` | `(text: str) -> List[dict]` — returns `{span, raw, value, unit, sentence}` for every `NUMERIC_CLAIM_RE` hit. | n/a | called by the two below |
| `is_structural_number` | `(raw: str) -> bool` — matches `STRUCTURAL_NUMBER_ALLOWLIST_RE` (series day counters, list ordinals, model names like `GPT-4` when that is the sourced topic). | n/a | called by `validate_no_number_without_source` |
| **`validate_no_number_without_source`** | `(text: str, source_context: str) -> Tuple[bool, List[str]]` — for each claim, normalize `value+unit` ("60 percent" → `(60,'%')`, "5 microseconds" → `(5,'us')`) and require a match in `source_context` **within ±80 chars of a subject keyword from the claim's sentence**. Empty `source_context` ⇒ any non-structural number fails. | **REGENERATE once** with a "describe qualitatively; no numbers" instruction; if still failing → **SKIP**. Never strip silently: removing "60" from "idle 60 percent of the time" yields a different false claim. | `src/scheduler.py:2007`, immediately after `sanitize_publish_text(final_text)` |
| **`validate_no_repeated_title`** | `(text: str, topic_title: str) -> bool` — case/punctuation-normalized; fails when the first ~200 chars contain the title twice, or when a question-form title is embedded mid-sentence. | **STRIP** the offending sentence deterministically, then re-run; if result `< 900` chars → REGENERATE → SKIP. | same gate, at `src/scheduler.py:2007` |
| **`validate_no_broken_template`** | `(text: str) -> bool` — `BROKEN_TEMPLATE_RE`. | **STRIP** the single matching sentence; re-run length check. | same gate, `src/scheduler.py:2007`; also apply at generation time in `generate_full_linkedin_article()` fallback `src/ai_generator.py:739-755` by removing line 741 and the `comp_str` injection at `:733`. |
| **`validate_no_absolute_claims`** | `(text: str) -> Tuple[bool, List[str]]` — `ABSOLUTE_CLAIM_RE` over body sentences (hashtags excluded). | **REGENERATE once** with "hedge all claims; state bounds and conditions"; then SKIP. | same gate, `src/scheduler.py:2007` |
| **`validate_sourced_proper_nouns`** | `(text: str, source_context: str, allowlist: set) -> Tuple[bool, List[str]]` — capitalized multi-word technical names / versioned names (e.g. `FlashAttention V3`, `Murmur3`, `PagedKV`) must appear in `source_context` or `allowlist`. | REGENERATE once; then SKIP. | same gate, `src/scheduler.py:2007`, and on `arch_spec` before `render_editorial_architecture_gif()` at `src/scheduler.py:1958-1965`. |
| **`validate_plan_evidence`** | `(plan: dict, source_context: str) -> Tuple[bool, List[str]]` — recursively validates every string in `post_text`, `first_comment`, `cover.*`, `slides[]`, `pages[]`, `framework.steps[]` with `validate_no_number_without_source` + `validate_no_absolute_claims`. | Reject the plan → try the next candidate in the loop at `src/scheduler.py:1829`; if none pass, return False. | `src/scheduler.py:1889`, directly after `carousel_plan = sanitize_plan(plan)` |
| **`evidence_gate`** | `(text: str, *, topic_title: str, source_context: str, allowlist: Optional[set] = None) -> Tuple[bool, str, List[str]]` — master wrapper; runs all five in order, applies the STRIP-only fixes, returns `(ok, final_text, violations)`. | Caller records a `skipped` `linkedin_post` event with `skip_or_error_reason = "; ".join(violations)` and returns `False`. | **Primary:** `src/scheduler.py:2007`. **Secondary:** `src/scheduler.py:2025-2027` for `first_comm`; `src/scheduler.py:452/535/911/1041/1377/1514` for X/Bluesky (pass `source_context=""` so all non-structural numbers fail). |

### 4.3 The single choke point (conceptual patch, not applied)

```python
# src/scheduler.py:2007 — replaces the existing line
cleaned = sanitize_publish_text(final_text)
ok_ev, li_text, ev_issues = evidence_gate(
    cleaned, topic_title=topic_title, source_context=topic_summary
)
if not ok_ev:
    self.tracker.record_event(
        action_type="linkedin_post", status="skipped",
        target_identifier="Evidence integrity gate",
        skip_or_error_reason="; ".join(ev_issues),
        duration_seconds=time.time() - start_time,
        is_dry_run=self.safety.dry_run,
    )
    return False
```

This one location receives every LinkedIn post: the autonomous path (`li_text` built at `:1871-1896`), `custom_text` (`:1683`) and `custom_topic` (`:1786`), all of which flow through `pre_publish_review_and_gate()` at `:1990` and then `:2007`. It must run **after** `sanitize_publish_text()` because brand stripping can join words, and **before** `automater.post()` at `:2046`.

### 4.4 Harden the gate that already exists

`LinkedInPortfolioManager.validate_article_quality()` (`src/linkedin_portfolio_manager.py:122-159`) should gain, in order:

1. `if not validate_no_number_without_source(text, source_context)[0]: return False, "Unsourced numeric claim"` — requires adding a `source_context` parameter to `pre_publish_review_and_gate()` (`:240-291`) and passing `topic_summary` from `src/scheduler.py:1990-1998`.
2. `if not validate_no_broken_template(text) or not validate_no_repeated_title(text, topic): return False, "Broken/repeated title template"`.
3. Add the strings `Understanding the real-world mechanics of`, `is one of the most critical fundamentals`, and `is one of the most critical` to the `placeholders` list at `:143`.

Without (1), the "Executive Quality Gate" remains a false assurance mechanism; every currently-shipped fabricated stat passed it.

---

## 5. "No number without source" — enforceable rule

**Rule statement:** *A published sentence may contain a quantitative claim only if the exact value, unit and subject of that claim are present in the retrieved source context for that post. Everything else must be written qualitatively. Structural numbers (series day counters, list ordinals, and version digits inside a sourced proper noun) are exempt.*

### Enforceable algorithm

1. **Carry the source.** `selected_trend` is already assembled at `src/scheduler.py:1888` with `{"title": …, "summary": summary, "url": …}`. The `summary` string is the source-of-truth block. Pass it as `source_context` through the gate. When ideation produced the topic (`ideate_autonomous_tech_topic()`, `src/ai_generator.py:1613-1773`), the only trustworthy source fields are `summary`, `golden_rule`, `pro_nuance` and any `live_news_signals` entry actually used. If `source_context` is empty, every numeric claim is a violation.
2. **Extract.** `extract_numeric_claims(draft)` returns every `NUMERIC_CLAIM_RE` match with its containing sentence.
3. **Normalize.** Map surface forms to a canonical `(value, unit)` tuple: `60 percent`/`60%` → `(60, "%")`; `5 microseconds`/`5µs` → `(5, "us")`; `300 percent` → `(300, "%")`; `10,000` → `(10000, None)`.
4. **Match.** For each claim, require the canonical tuple **and** at least one subject keyword from the claim's sentence to appear in `source_context` within ±80 characters. This prevents "the source mentioned 60% of *something else*" from laundering an unrelated stat.
5. **Exempt.** `is_structural_number(raw)` allows only `Day NN/NN`, `Step N`, leading `N.` ordinals, and version digits in a name already present in `source_context` or `allowlist`. No other exemption.
6. **Act.** One regeneration with an explicit qualitative-only instruction, then **skip the post**. There is no "strip the number" fallback — partial stripping creates new false claims (e.g. "sitting idle of the time").
7. **Log.** Record the rejected claim's exact text in `recent_events[].skip_or_error_reason` so violations are auditable instead of silently disappearing.

### Prompt change to reduce regeneration churn (secondary, not a substitute)

Copy the existing strong sentence from `generate_linkedin_carousel_plan()` (`src/ai_generator.py:556`) into **every** LinkedIn generating prompt — `generate_full_linkedin_article()` (`:695-720`), `generate_educational_notes_plan()` (`:1188`), `generate_comparison_plan()` (`:1409`), `generate_linkedin_take()` (`:413-475`), `generate_ai_series_lesson()` (`:980`):

> "Use only facts present in the topic or context. Never invent a number, date, name, quote, funding amount, or study result. If a metric is not provided, describe the risk or the action qualitatively instead."

Also rewrite the metric-hungry hook at `src/ai_generator.py:702-703` from "Start with an eye-opening metric…" to "Start with the single most concrete *sourced* fact in the context; if none exists, open with the mechanism." And change the example hook at `:429` to remove the fabricated `40+ hours` / `260+ models`.

---

## 6. What this audit did not change

No production file was edited. `src/ai_generator.py`, `src/growth.py`, `src/scheduler.py`, `src/linkedin_portfolio_manager.py`, `trial_metrics.json` and all history files are untouched. The only artifact created is this report.
