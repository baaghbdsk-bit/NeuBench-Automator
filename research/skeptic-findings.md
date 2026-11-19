# Skeptic Findings — Red Team

Date: 2026-11-20. Scope: kill bad recommendations before they ship. Audience: engineers on a
real public personal profile. Trust loss here is irreversible: an engineer who catches one
invented number does not quietly come back.

## 0. The premise is broken before we argue tactics

"Increase engagement anyhow" is currently **untestable**. This repo does not collect the data
that would tell us whether engagement changed:

- `data/growth_baseline.json:3` — "No platform analytics API is connected, so reach,
  impressions, engagement rate, watch time, and demographics are NOT captured."
- `data/growth_baseline.json:92-97` — no impressions, reach, engagement rate, saves, shares,
  watch time, follower history, or experiment log.
- `AUDIT_REPORT.md:24` — `/api/stats` reports X followers **hardcoded (20)** and impressions
  **estimated as cycles × 4500**; LinkedIn/Reddit/Threads stats are constants or derived.
- `data/growth_baseline.json:10` — LinkedIn has **80 followers**. At this size, most
  engagement changes are statistically indistinguishable from noise.

Consequence: if the swarm ships a tactic next week and the dashboard "goes up," that is a
number we invented ourselves. We will have optimized a hallucination. **Instrumentation is a
prerequisite to any experiment, not a follow-up task.** Until then the only honest verdict
available is "not rejected," never "working."

## 1. Predicted swarm recommendations and their actual failure modes

| Likely recommendation | Why the swarm will propose it | Dominant failure mode | Specific evidence from this repo | Verdict |
|---|---|---|---|---|
| **Stronger hooks / bigger "scary numbers"** | "First line must stop the scroll"; feedUX research says concrete numbers work | **Trust loss + legal/reputational.** Numbers are the account's original sin and the generator structurally demands them | Shipped: *"Your LLM inference cluster is likely wasting 60 to 80 percent of its GPU memory on empty air."* (`trial_metrics.json:1248`); *"API provider variance ... hits 40% under real workloads."* (`:48`); *"p99 latency spikes by 300 percent"* (`:348`); *"NeuBench telemetry on 260+ models shows..."* (`:918` — authority claim with no telemetry in repo). `src/ai_generator.py:781` instructs: *"METRICS (Exactly 3 bars): ... with concrete units"*, and `:796-799` requires "Realistic value with units" — i.e. the generator is told to manufacture precise numbers | **Keep hooks. Kill invented numbers.** Veto detail in §5 |
| **Comment bait** ("thoughts?", "agree?", "drop a 🔥", engineered first-comment question) | Cheapest visible lever; comments are the most controllable metric | **Trust loss + platform penalty.** Bait comments are low-signal; engineers recognize and punish them; LinkedIn demotes engagement bait | Hard constraint already bans "thoughts?" (`agents/README.md:30`). `src/ai_generator.py:1106-1128` generates a first comment whose structure is *"An open question asking developers how they handle this in production"* — an engagement device, not a resource | Ban as an *engagement* device. A first comment may add a source, a caveat, or a real code snippet; never a question written to farm replies |
| **More visuals** (more carousels, more GIFs) | "Attachments earn the stop-scroll and saves" | **Audience mismatch + maintainer time.** Decorative diagrams and invented metric bars are worse than text-only for systems engineers; no attachment-level measurement exists | Generator requires exactly 3 "metric" bars with made-up units (`ai_generator.py:781,796-799`). `growth_baseline.json:92-97` has no save or attachment data, so "visuals work" cannot be shown. Carousel/GIF output is already in `linkedin_post_history.json:844,854,864,...` | Allowed only if every number on the slide is sourced. No decorative GIFs. Text-only is a legitimate outcome |
| **More automation** (6 peer comments/day, auto-replies, hot takes, more AI generation) | "Engagement velocity" is a lever; reply targets already wired | **Legal/reputational + trust loss.** Autonomous contrarian posting on a named personal profile is an unbounded risk; the pipeline also fails constantly | `src/ai_generator.py:1132-1144` `generate_debate_comprehension`: *"savage contrarian take"*, *"unapologetically unfiltered, funny, and provocative"* for political/religious/cultural debates. `config.py:23-28` targets `viral_culture, work_life_debates, wealth_finance`. `trial_metrics.json:15-16` — **170 failed operations, 554 skipped**; the same Playwright error repeats dozens of times (e.g. `:29,59,89,129`). `growth_baseline.json:51-52` — 1 reply succeeded vs 47 skipped | Kill autonomous debate/hot-take generation outright. Peer comments stay human-reviewed. Fix the pipeline before scaling it |
| **More posting** (raise LinkedIn above 1/day for "surface area") | Volume is the simplest lever to pull | **Platform penalty + audience mismatch.** Reach is killed by cadence before content matters; volume produces off-niche filler | `agents/README.md:15` — *"8 posts in 27 hours (cadence killed reach before content mattered)."* `config.py:59,67` and `.github/workflows/linkedin_automater.yml:78-79`, `x_automater.yml:94-97` already cap LinkedIn at 1/day, 12h — yet `trial_metrics.json:39,69,139` log *"LinkedIn daily cap reached (4/2)"*, *"(5/2)"*, i.e. the running behavior overshot. `growth_baseline.json:61` — **43% off-niche** content, including *"tata motors share price"* (`linkedin_post_history.json:368`), *"hindalco share price"* (`:378`), *"bosch share price"* (`:768`), *"sbi share price"* (`:818`) | Hard cap: 1 post/day, 12h min. Raising it is not an experiment we are allowed to run |

## 2. Hard do-not-do list

1. **Never publish a number that is not sourced in the post itself or in a source we can paste
   on demand.** Includes ranges and "up to" hedges: "60 to 80 percent" (`trial_metrics.json:1248`),
   "up to 40% variance" (`:428`), "300 percent" (`:348`), "260+ models" (`:918`). Also kill
   pseudo-authority framing like "NeuBench telemetry shows…" when no telemetry exists
   (`growth_baseline.json:3`). Reason: the first engineer comment will be "source?" and the
   comment thread — not our post — becomes the artifact people remember.
2. **Never raise LinkedIn cadence above 1 post/day or shorten the 12h cooldown.** Reason:
   cadence already killed reach once (`agents/README.md:15`); caps exist in `config.py:59,67`
   and the workflows; the trial log shows the cap being breached (4/2, 5/2).
3. **Never ship "What is X?", "Understanding the real-world mechanics of X", or the
   scenario→scary number→explainer skeleton twice in a row.** Reason: the audit flagged seven
   posts with the same opener (`agents/README.md:16`); titles in `linkedin_post_history.json`
   repeat it ("What is an Inverted Index?" at `:318,968,1068`; "What is a Bloom Filter?" at
   `:418,1138`; "Demystifying…" at `:466,617,628,927,928,937,998,1008`). Repetition is how a
   real account advertises that it is a bot.
4. **Never use engagement bait or a reply-farming question as the close.** No "thoughts?",
   "agree?", emoji gates, "comment X for Y", or auto-generated open question
   (`ai_generator.py:1106-1128`). Reason: banned by charter (`agents/README.md:30`), and bait
   comments poison the very metric we are trying to improve.
5. **Never post off-niche: stock prices, election/politics, celebrity news, cultural flame
   wars, or "savage contrarian" takes.** Reason: 43% off-niche already shipped
   (`growth_baseline.json:61-70`); `config.py:26` explicitly targets `viral_culture` and
   `wealth_finance`; `ai_generator.py:1132-1144` can generate unfiltered political hot takes.
   On a personal professional profile this is reputational and possibly legal exposure, not
   growth.
6. **Never let generated text publish without deterministic pre-publish validators.** The
   current sanitizer only strips brands/URLs and repairs dead labels (`src/growth.py:40-61`);
   it has **no number check**. Reason: broken copy already shipped publicly — *"Understanding
   the real-world mechanics of What is a Bloom Filter? is one of the most critical..."*
   (`agents/README.md:18`). A regex that blocks "What is X" openers, unsourced numerals,
   and duplicate title text is cheaper than a public correction.
7. **Never declare a win from `/api/stats`, `trial_metrics.json` counters, or any other
   estimated/hardcoded metric.** Reason: `AUDIT_REPORT.md:24`, `growth_baseline.json:3,92-97`.
   Only real platform analytics count.
8. **Never auto-publish AI replies/comments to third parties on controversial or financial
   content, and never raise the 6/day peer-comment cap as a growth lever.** Reason:
   `linkedin_engagement.yml:69-70` sets 6; autonomous replies multiply any single bad take by
   six and attach it to someone else's audience.
9. **Never recycle a near-duplicate topic within 30 days.** Reason: Jaccard threshold 0.55
   (`src/growth.py:119-131`) is too loose for retitled clones; clusters already recorded:
   agent-memory-observability ×6, context windows ×4, B-tree-vs-LSM ×3, CPU-vs-GPU ×3
   (`growth_baseline.json:71-79`), plus three io_uring/kernel-bypass posts in 7 hours
   (`agents/README.md:19`).
10. **Never ship a visual containing an invented metric bar, and never add visuals to hide a
    weak post.** Reason: `ai_generator.py:781,796-799` asks for "Realistic value with units"
    — invented precision rendered as a chart is *more* credible and *more* damning than a bad
    sentence. Text-only is acceptable.
11. **Never scale output while the pipeline is broken.** Reason: 170 failed operations and 554
    skips (`trial_metrics.json:15-16`), with one identical Playwright error repeated across
    dozens of cycles (`:29,59,89,129,...`) and a 404 model failure at `:499`. More automation
    here produces more failures, not more engagement.

## 3. Evidence thresholds before any tactic is accepted as "working"

**Gate 0 — Instrumentation (blocking).** Capture, from the real LinkedIn post page, for each
post: timestamp, impressions, reactions, comments (with text), saves, reposts, profile views,
follower delta. Replace the `null`s in `growth_baseline.json:13-16,92-97`. If this is done
manually by the account owner once per post at 48h, that is acceptable — estimated dashboard
numbers are not. No tactic is evaluated before this exists.

**Gate 1 — Pre-register before launch.** Write down, in `research/experiment-log.md`:
hypothesis, single changed variable, primary metric, minimum effect worth keeping, and kill
criteria. If the criterion is written after seeing the result, the result is discarded.

**Gate 2 — Sample size.** Minimum **20 published posts in the treatment arm** and **20 in the
control** (trailing-20 pre-change baseline when we cannot run simultaneous arms). At 1
LinkedIn post/day that is ~40 days for a clean A/B, so in the first 30 days we can only run
**one change at a time** against a trailing baseline and must accept "inconclusive" as an
outcome. Read comment-rate only after **≥1,000 impressions per arm or ≥30 substantive
(non-emoji, non-one-word) comments per arm**; below that, a comment delta is noise. With 80
followers (`growth_baseline.json:10`) this threshold may not be reachable in 30 days — that
is a reason to keep running, not to lower the bar.

**Gate 3 — Time window.** Measure each post at **48h** (LinkedIn's engagement window) and
**7d** (long-tail saves/profile visits). Interim read at 14 days **only** for guardrail
breaches, never for declaring a win. Final decision at 30 days.

**Gate 4 — Comparison.** Within-account only: same day-of-week/time slot, same topic pillar,
same format, cadence held at 1/day. No cross-platform comparisons, no "industry average,"
no Bluesky-to-LinkedIn extrapolation. Primary metric:
`(comments + saves + reposts) / 1,000 impressions`, plus `profile views per post`.
Secondary: follower delta per post. Guardrails that must stay at zero: unsourced numbers,
off-niche topics, brand remnants, broken copy, "unfollow"-type comments.

**Gate 5 — Kill rules (automatic, no debate).**
- Any trust guardrail breach → kill immediately, regardless of engagement.
- Impressions down >20% vs trailing-20 baseline for **5 consecutive posts** → platform
  penalty → kill and revert.
- Comment count up but saves, profile views, and followers flat, and comments are one-word
  or bait-shaped → treat as bait → kill.
- Tactic costs the maintainer >30 min/week → kill; this is an automated account, not a second
  job.

## 4. Three most likely ways this fails in 30 days

1. **The measurement illusion (most likely).** Someone ships a hook/visual change, the
   dashboard shows a gain, and the team declares victory — but the gain comes from hardcoded
   or estimated numbers (`AUDIT_REPORT.md:24`) or from a small-sample swing at 80 followers
   (`growth_baseline.json:10`). Real engagement is flat, nothing was learned, and we have
   added another unsourceable claim to the account's history. Early warning: anyone saying
   "it worked" without quoting impressions, comments, saves, and profile views per post.

2. **The fact-check pile-on (most damaging).** A "stronger hook" built on an invented number
   lands on an engineer's feed: "60 to 80 percent of GPU memory on empty air"
   (`trial_metrics.json:1248`) or "NeuBench telemetry on 260+ models" (`:918`). The top
   comment is "source?", the post gets quoted with the number highlighted, and the account's
   already-documented pattern of invented stats (`agents/README.md:17`) makes "one-off typo"
   implausible. No delete-and-apology restores that. Early warning: any draft containing a
   percentage, a "up to", a range, or a telemetry claim that cannot be pasted into the post.

3. **Automation and volume compound into irrelevance (most expensive).** Pressure to "post
   more / automate more" raises output against a pipeline with 170 failures and 554 skips
   (`trial_metrics.json:15-16`) and an unfixed Playwright error repeating every cycle
   (`:29,59,89,129`). More volume means more near-duplicate topics (clusters in
   `growth_baseline.json:71-79`), more off-niche stock-price filler (43%, `:61-70`), more
   reach suppression from broken cadence (`agents/README.md:15`), and more maintainer time
   spent firefighting. The account is still at ~80 followers and is now also known for noise.
   Early warning: "daily cap reached (4/2)" or "(5/2)" appearing again in the log
   (`trial_metrics.json:39,69,139`).

## 5. Veto outright

**I veto the "scary-number hook": any recommendation whose stop-scroll power depends on an
invented, rounded, hedged, or unverifiable statistic — including "up to X%", "60 to 80
percent", "300 percent", "5 microseconds", and pseudo-authority framing such as "telemetry
shows..." on numbers we did not measure.**

This is not a "cap it and test it" item. It is the one route where "anyhow" converts directly
into irreversible, audience-specific harm: engineers are uniquely likely to check the number,
the generator is structurally primed to produce one (`src/ai_generator.py:781,796-799`),
and the account has already shipped several (`trial_metrics.json:48,348,918,1248`;
`agents/README.md:17`). It also violates hard constraint #2 (`agents/README.md:28`) and would
be rendered even more credible — and therefore more damaging — if we put it on a carousel
bar. Everything else in this document can be bounded with a cap or an experiment. This one
cannot.
