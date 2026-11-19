# Swarm Synthesis — LinkedIn First, One Plan

Seven agents, seven reports. This file resolves the conflicts and is the only
plan we execute from. The individual reports are evidence, not policy.

## Blunt verdict

The account has three separate failures, and they compound:

1. **Trust failure** — invented statistics shipped as fact in at least 9 of 25
   posts. The hard-coded fallback literally prints the topic title twice.
   Visual fallbacks hard-code fake metrics (`900 GB/s via NVLink`, `<120 nanoseconds`).
2. **Voice failure** — 12/25 openers use "Your/You", 15/25 lead with a number,
   1/25 contains any first-person POV. The personality exists in the X drafts
   and never reaches LinkedIn.
3. **Measurement failure** — we track attempts and skips (52.6% of events are
   skips), not comments, saves, profile views or follows. `/api/stats` uses
   hardcoded and estimated values. We cannot know if anything works.

Cadence was a fourth failure (8 posts in 27h). **That one is already fixed** —
verified in current code: `config.py` 1/day + 720m, `x_automater.yml` and
`linkedin_automater.yml` 1/day + 720m. The "cap 2 / 180m" in the growth report
is historical evidence from the broken period, not the current state. Do not
"fix" it again.

## Where the agents disagreed, and my call

| Disagreement | Call |
|---|---|
| Growth strategist: freeze content work until instrumented. Voice/hook agents: fix copy now. | **Both, as separate tracks.** Trust defects and the deterministic gate are correctness, not experiments — ship now. Hook/voice changes are experiments — one variable at a time, never declared a win before instrumentation. |
| Hook agent: first comment adds detail + a narrow question. Skeptic: a question written to farm replies is bait. | **First comment = new technical detail or caveat only. No question by default.** The body already carries exactly one genuine answerable question. This removes duplicate questions and bait risk. |
| Visual designer: carousels can be fixed and kept. Skeptic: invented metric bars on a slide are worse than text-only. Growth: 51% prefer text posts. | **Default to text-only.** Keep the PDF carousel only after fake metrics are removed and the rendering gates work. Kill the flow-GIF attachment entirely. |
| Voice editor: every post needs "I". Hook psychologist: first line must be declarative with anchor + consequence. | **Combine:** first line = first-person consequence with a named mechanism. No question, no definition, no unsourced digit. |

## Wave 0 — correctness, ship now (not experiments)

1. **One evidence gate.** New `src/evidence_guard.py` with `evidence_gate(text, topic_title, source_context)`. Call after `sanitize_publish_text(final_text)` at `src/scheduler.py:2007`, before `automater.post()` at `:2046`. Enforce:
   - no numeric claim unless value + unit + subject appear in the sourced context (structural numbers exempt);
   - no broken template / repeated title (`Understanding the real-world mechanics of …`, `is one of the most critical fundamentals`);
   - no absolute claims (`guaranteed`, `zero`, `eliminate`, `100%`);
   - no unsourced versioned proper nouns (`FlashAttention V3`, `Murmur3 Hashers`, `PagedKV Ring Buffer`).
   - **On failure: regenerate once with a qualitative-only instruction, then SKIP and log the exact violation.** Never silently strip a digit — "idle 60 percent of the time" → "idle of the time" is still false.
2. **Apply the same gate to plans** at `src/scheduler.py:1889` (post_text, first_comment, cover, slides, pages) and to the visual spec before `render_editorial_architecture_gif()` near `:1958`.
3. **Delete the defect sources in `src/ai_generator.py`:** the metric-hungry hook at `:702-703`, the hard-coded fallback at `:739-755` (especially `:740-741`), fake visual metrics at `:829-975`, fake schema examples at `:1459-1462` and `:1557-1561`, the fabricated `40+ hours / 260+ models` example at `:429`, and stale tracker/thoughts strings at `:373` and `:464`. Copy the existing strong "never invent a number" sentence from `:556` into every LinkedIn prompt.
4. **Harden the theatre gate:** `LinkedInPortfolioManager.validate_article_quality()` (`src/linkedin_portfolio_manager.py:122-159`) currently checks length and placeholders only. Add the gate checks and pass `topic_summary` through `pre_publish_review_and_gate()` (`:240-291`). Add the broken-template phrases to its placeholder list at `:143`.
5. **Instrument outcomes (Day 0 baseline before any content experiment):** minimal real log `data/linkedin_outcomes.json` with timestamp, post id, `visual_format`, impressions, reactions, comments (text), saves, profile views, follower delta — captured at 48h and 7d manually from LinkedIn analytics (no invented API). Make `linkedin_engagement_history.json` and `data/x_followers.json` real, persisted artifacts. Add `visual_format` to every post record — 83/120 posts currently have none.
6. **Lock the cadence fix with a test** so `1/day + 720m` cannot regress. Audit `force=True` (`src/scheduler.py:1587-1595`) — it intentionally bypasses caps; document it, don't silently allow it in scheduled runs.

## Wave 1 — content and attachment, one variable at a time

7. **Voice + hook gate** (one prompt change + one regex, `src/ai_generator.py:695-720`):
   - first line 60–160 chars, first-person, named mechanism, consequence marker;
   - automatic reject: `What is `, `Understanding the real-world mechanics of`, `Your … yet/but`, `Every`, `Imagine`, `In today's`, `game changer`, `unlock`;
   - exactly one closing question ≤120 chars, answerable in ≤12 words, sharing the hook's topic anchor; no `thoughts?`, no `what do you think`;
   - one falsifiable stance in the first three lines; no `it depends` hedging;
   - ≤3 hashtags (currently up to 5 at `src/scheduler.py:2010-2019`).
   - Ship gate: voice rubric ≥7/10, POV ≥1, clean open mandatory (`research/linkedin-voice-findings.md §6`).
8. **First comment** (`src/scheduler.py:1892-1895` and the re-derivation at `:2023-2027` — both sites): 180–320 chars, one new engineering detail or decision rule, zero links, zero numbers, no question. Never referenced from the body. Note `generate_first_comment_value_drop()` at `src/ai_generator.py:1106-1130` is currently unused — either wire it with the new spec or delete it.
9. **Attachment (do these in order):**
   - Stop attaching the flow GIF's frame 0 (`src/linkedin_diagrams.py:776-778`): make `animated_flow_gif` posts **text-only** until the preview carries information.
   - Remove invented metric bars from the visual spec (`src/ai_generator.py:781,796-799` and fallbacks); if numbers are not sourced, the slide states the mechanism qualitatively.
   - For the PDF carousel only: save slide 1 as `{base}_hero.png` to revive the dead fallback (`linkedin_visuals.py:816-852`), wire `assets["alt_text"]` into the attachment (`scheduler.py:1934-1945,2050`), fix the `pages >= 4` gate (`:1935`) and the topic-affinity validator (`:165-205`).
   - Remove "Save this" begging and emoji decoration from visuals; keep neutral footer + page number.
   - Verify every attachment at 320px before shipping.

## Wave 2 — distribution, after Wave 0 measurement exists

10. Make the separated `linkedin-engagement` workflow demonstrably produce 4–6 substantive peer comments/day on **AI-engineering practitioners** (~10k–100k followers who reply), not celebrities/brands. Verify `linkedin_engagement_history.json` grows.
11. Reply to every substantive comment on our posts within 2 hours (correlates with higher engagement; it is also basic respect). Currently no reliable tracking of this.
12. Confirm the staged creator bio/headline is actually live on the profile — highest ROI × ease, likely already done.
13. Only then test one posting-time shift within the single daily slot. The two external datasets conflict (evening vs midday), so use our own 48h data.

## Kill criteria (apply literally, no extending windows)

- Any trust guardrail breach (unsourced number, off-niche topic, brand remnant, broken copy) → kill immediately.
- More than 1 LinkedIn post on any 2 days after the guardrail fix → guardrails still broken; stop all scaling.
- Median <1 substantive comment across 10 posts → distribution dead; pivot entirely to peer comments.
- `linkedin_engagement_history.json` still absent/empty after 7 days → workflow is not executing; stop calling it a growth channel.
- Impressions down >20% vs trailing-20 baseline for 5 consecutive posts → platform penalty; revert.
- Comments up but saves/profile views/followers flat and comments are one-word/bait-shaped → bait; kill.
- Any tactic costing >30 min/week of maintainer time → kill.

## What I will not do

No scary-number hooks. No engagement bait. No >1 LinkedIn post/day. No political,
stock-price, celebrity or "savage contrarian" content. No decorative GIFs or
unsourced metric bars. No declaring a win from `/api/stats`, `trial_metrics.json`
counters or any estimated number. No cross-posting the same explainer 15 times.

## One-line answer to "quality vs shipping"

These are four deterministic guards (evidence gate, prompt hook gate, text-only
flow format, real outcome log) — roughly one focused implementation pass, not a
review process. After that we ship and measure. I am not asking for a design
committee.
