# X Voice & Niche Findings — creator account (AI engineering / LLM benchmarks / dev tools)

**Role:** X voice editor (blunt mode). **Scope:** 𝕏 only. Bluesky is out of scope for this file.
**Evidence base:** `trial_metrics.json` → `recent_events` (500 events); topic banks in `src/trend_hunter.py`; generator in `src/ai_generator.py`; publishing path in `src/scheduler.py`; gate in `src/growth.py`.
**Method:** parsed `trial_metrics.json` with PowerShell `ConvertFrom-Json`. "Content-bearing draft" = `action_type == "original_post"` AND non-empty `content_preview`. Regex predicates are stated with each count. No number in a rewrite or hook example is invented; where a number is dropped from a source claim, I say so.

**Honesty rule applied:** a "verbatim shipped quote" below is quoted *exactly as stored*, including truncation. `content_preview` is `prepare_x_text(text)[:120]` (`src/x_state.py:188`, `:227`), so every preview is cut at 120 characters (stored lengths here: 120–126, the excess is mojibake bytes). Mojibake such as `â€™` for `'` is in the stored string. I mark cuts as `[cut@120]`.

---

## 1. Blunt verdict

There is no X voice problem in the sense of "no personality." There is a **supply problem and a truth problem**.

1. The generated X text is loud, first-person, and sarcastic — but it is a **single roast template run on one topic**: "Paying Silicon Valley rent to watch AI hallucinate a Python loop..." All 74 content-bearing `failed` `original_post` events share the **same target**, `Frontier Reasoning Drift & Cost per 1M Tokens (DeepSeek vs Claude vs Gemini)`, and the **same failure reason**, `BrowserType.launch: Executable doesn't exist at /home/runner/.cache/ms-playwright/chromium_headless_shell-1255/...`. Those are retries of one engineering brief that never published. They are not 74 pieces of content.
2. The posts that **actually shipped** (`status == "success"`, 23 events) are mostly **not about AI at all**: football, basketball, cricket, taxes, politicians. The "voice" that reached the feed is sport-roast comedy, not a builder's opinion.
3. Both failures are *designed in*: `X_UNHINGED_SYSTEM_PROMPT` licenses "wider internet culture" (`src/ai_generator.py:10`) and demands "one concrete detail: a number, a tool, a model name, a price" (`:14`), while the main X prompt `generate_hot_take` (`src/ai_generator.py:194-211`) says "Lead with the sharpest specific claim, **number**, or contradiction" and, unlike `generate_ai_take` (`:286` "Never invent numbers") and the LinkedIn article prompt (`:700`), **contains no prohibition on invented numbers**. `evidence_gate` rejects unsourced numbers (`src/growth.py:227-238`, `:294-320`) but is wired only into LinkedIn (`src/scheduler.py:1913`, `:2059`). X and Bluesky ship ungated.

---

## 2. Counts (with the exact predicate used)

All counts over `trial_metrics.json` → `recent_events`, current file (`trial_meta.last_updated` = `2026-11-19T20:01:54.425550+00:00`).

| Quantity | Count | Basis / verbatim anchor |
|---|---|---|
| Total events | 500 | `recent_events` length |
| `original_post` events | 176 | status: 79 failed, 23 success, 74 skipped |
| `original_post` with non-empty `content_preview` | 97 | 74 failed + 23 success; all `is_dry_run=false`. Skipped events carry no preview. |
| Failed drafts sharing ONE target + ONE Playwright error | **74 / 74** | target `Frontier Reasoning Drift & Cost per 1M Tokens (DeepSeek vs Claude vs Gemini)`; reason `BrowserType.launch: Executable doesn't exist at /home/runner/.cache/ms-playwright/chromium_headless_shell-1255/chrome-headless-shell-linux64/chrome-headless-shell` |
| Shipped (`success`) posts | 23 | — |
| Shipped posts with off-niche **targets** (sport / cinema / finance / politics / meme) | **20 / 23 (87%)** | verbatim targets: `u.s. soccer`, `erling haaland`, `Politicians on social media PR teams`, `uruguay vs dominican republic`, `Income tax vs public infrastructure`, `ball state vs ohio`, `bosnia and herzegovina national football team vs romania national football team standings`, `rudy gobert`, `mexico vs jamaica`, `unlv vs kansas`, `dylan harper`, `akash deep`, `central mi vs buffalo`, `mavericks vs warriors`, `Religious dogmatism vs basic human decency`, `tyler herro`, `byu basketball`, `will richard` (plus 2 garbled targets). On-niche shipped: `Frontier Reasoning Drift & Cost per 1M Tokens...`, `The AI bubble and pitch deck madness`, `AI will replace coders vs Indian IT bodyshopping` — **3**. |
| Shipped off-niche content, verbatim | — | `Calling it "soccer" while the rest of the planet treats football like an actual religion is the ultimate American superp [cut@120]` · `Erling Haaland is literally just a 19th-century Viking peasant who accidentally time-traveled into an elite football con [cut@120]` · `Gujarat Titans are the corporate presentation that somehow gets a promotion over the guy who actually built the company.` |
| First-person POV (`\b(I\|my\|me\|we\|our\|mine\|myself)\b`) | **50 / 97** content-bearing drafts (45 failed, 5 success) | verbatim: `Me explaining to my landlord that I can't pay rent this month because my AI coding agent went on a 260-model bender and [cut@120]` (stored with `canâ€™t`) |
| First-person in shipped posts that is actually a *stake* | **~0 / 23** | the 5 hits are incidental: `...tweet "we cooked" right before passing a bill to ban the internet is [cut@120]` (quoted phrase), `Watching Mexico vs Jamaica is basically a stress-test for my heart rate while pretending I understand tactical football.` (joke setup), `Watching Dylan Harper ball out while my biggest athletic achievement today is successfully dodging human contact at the [cut@120]`, `Paying 35% tax just to fund a DIY lifestyle where I also have to buy my own water, power, security, and roads. At this p [cut@120]`, `"will richard" ... module we all have to [cut@120]` |
| Any digit in preview | 38 / 74 failed, 11 / 23 success | — |
| Strict currency/unit number pattern (`\$\d`, `\d+\s*(k\|M\|million\|bucks\|%...)`, `\d+\s*(minutes\|hours\|tokens\|model)`) | 27 / 74 failed, 1 / 23 success | verbatim invented figures: `Paying $50 to watch an AI overthink a bug for 10 minutes just to suggest \`npm install left-pad\`. Truly we are living in [cut@120]`, `Spending $400 on API tokens just for Claude to hallucinate a python script that deletes my entire system 32 folder. We t [cut@120]`, `Dropping $40 per 1M tokens just so Claude can write a React component that still invents a new JavaScript framework out [cut@120]` |
| Spelled-out invented quantities | present, exact count **not verifiable** | `...for 4 minutes is the 2026`, `...for three hours while draining my entire bank acc [cut@120]`, `...hallucinate a missing semicolon for five minutes. The future is here a [cut@120]` |
| "thoughts?" / "what do you think" / "agree?" in preview | **0 / 97** | — (but preview is cut at 120 chars; see §8) |
| Hashtag in preview | 1 / 97 | `paying Silicon Valley rent with my prompt tokens just to watch an AI hallucinate a Python loop is my Roman Empire. #AI # [cut@120]` — a cut-off double hashtag |

### Dispute with the manager's baseline

The brief states "43% off-niche" and "51/177 drafts with first-person voice." **I could not reproduce either number from the current file.** I get 176 `original_post` events (not 177), 97 with content, and 50 first-person by the stated regex (54 if I scan every event with a preview, not just `original_post`). The "51/177" figure appears verbatim in `research/linkedin-voice-findings.md:14`, so it is a carried-forward figure from an earlier snapshot/denominator, not a fresh measurement. The 43% figure is also not reproducible; my measured off-niche rate is **87% of shipped posts (20/23)**, or 20/97 (21%) if failed drafts are included in the denominator. **Denominator matters more than the percentage here.** Report both, not one.

---

## 3. Does the prompt produce the voice it claims?

**No — it produces the opposite of the constraints.**

- `X_UNHINGED_SYSTEM_PROMPT:10` promises a "builder's lens" but explicitly adds "You also comment on wider internet culture." The shipped feed proves which half wins: `Watching Ball State and Ohio battle it out to see who gets to [cut@120]` and `Checking Bosnia and Herzegovina vs Romania standings is the male equivalent of reading horoscopes [cut@120]` are not a builder's lens on anything. The off-niche supply is code-backed: `get_x_unfiltered_topics()` contains `Election season promises vs reality`, `Income tax vs public infrastructure`, `Religious dogmatism vs basic human decency` (`src/trend_hunter.py:1783-1787`), `get_casual_topics()` injects Google Trends spikes (`src/trend_hunter.py:1284-1294`), and `scheduler.py:1275-1278` + `:1307` fall back to both when trends are thin. The 70% growth-topic blend at `scheduler.py:1268-1272` is good intent but is defeated by the fallback.
- `X_UNHINGED_SYSTEM_PROMPT:14` ("Every post needs one concrete detail: a number, a tool, a model name, a price") plus `generate_hot_take`'s "Lead with the sharpest specific claim, number, or contradiction" (`src/ai_generator.py:203`) with **no "never invent numbers" line** (contrast `:286`, `:700`) is a direct instruction to fabricate. The 74 failed drafts are the output: `Paying a month's rent to watch an AI overthink a 5-line bug for 40 minutes just to suggest turning it off and on again. [cut@120]`.
- `generate_hot_take:205` says "Contrarian or useful, never neutral. The reader should want to reply or quote it." That is a mechanism, not a voice. Without a factual spine it collapses into "tech bros cry" / "Bro really..." roasts. `generate_sniper_reply:223-228` asks for "savage wit or devastating humor" and feeds the same system prompt, so the roast register is reinforced everywhere.
- The prompt's "No hashtags unless one is truly natural" (`:206`) is barely exercised (1/97 previews) — not a problem, just do not add hashtags for reach.
- LinkedIn's `evidence_gate` (`src/growth.py:294-320`) checks unsourced numbers, banned openers, absolute claims, repeated titles and a single non-bait question. Both call sites are LinkedIn (`src/scheduler.py:1913`, `:2059`, the latter records `action_type="linkedin_post"` at `:2068`). X and Bluesky have no equivalent. This is the single highest-leverage gap.

---

## 4. Exact X content spec for engagement

This is a proposed spec, not a description of current behavior. No engagement telemetry exists (§8), so the "why" is mechanism, not measured outcome.

- **Hook shape.** First line = an arguable claim or a first-person consequence with a named mechanism. Not a question, not a title echo, not "Paying X rent to watch AI..." (that skeleton recurs across the 74 failed drafts). `validate_no_banned_openers` already rejects question-first lines and banned openers for LinkedIn (`src/growth.py:241-249`); adopt the same for X.
- **Length.** ≤240 characters (`src/ai_generator.py:15`, `:204`). Cannot verify actual shipped lengths — preview is cut at 120 (§8).
- **One idea.** One claim, one mechanism, one concrete detail drawn from the supplied topic context. If the context has no number, do not introduce one. `validate_no_number_without_source` (`src/growth.py:227-238`) is the right test.
- **What earns a quote-tweet.** A falsifiable, specific claim a practitioner can screenshot and argue with. Real bank example: `Endpoint reliability and error rates matter more than leaderboard scores once a feature is in production.` (`src/trend_hunter.py:1054`).
- **What earns a reply.** End with one short, answerable question about a mechanism, or a claim with a clear counter-position. Never "thoughts?" (`src/ai_generator.py:17`). Example: `Which part of your stack is actually yours?`
- **Hashtag.** At most one, only if natural (`src/ai_generator.py:16`). Default: zero. No links, no brand, no emojis at the start (`:206`); charter adds no outbound URLs in bodies (`agents/README-X-BLUESKY.md:11`).

---

## 5. Ten ready-to-use hook patterns (examples drawn from our own topic bank)

Every example below is either verbatim from `src/trend_hunter.py` (line cited) or explicitly marked "adapted." **No invented numbers.** Where the bank's own number would have made the example unfree of numerals, I dropped it and said so.

1. **Hidden-cost reversal** — "The expensive part is not [obvious]. It is [overlooked]."
   `Most production AI features do not need a frontier model. The expensive part is usually the retry loop, not the answer.` — `src/trend_hunter.py:1812` (verbatim).
2. **Leaderboard contradiction** — "It can win [status game] and still fail [real condition]."
   `A model can win every public benchmark and still feel slow in production because p95 latency and queueing are not on the leaderboard.` — `:1813` (verbatim).
3. **Nobody prices it** — "Everyone argues about [visible]. Nobody prices [invisible]."
   `Everyone talks about model quality and nobody talks about the idle GPU bill between requests.` — `:1816` (verbatim).
4. **Premature fix** — "Teams jump to [heavy solution] before [cheap prerequisite]."
   `Teams jump to fine-tuning before they have clean examples. Most of the time a better prompt and a smaller model is the cheaper win.` — adapted from `:1817`; bank's "50 clean examples" number dropped.
5. **First-person correction** — "I stopped [old behavior] when [mechanism] failed."
   `I stopped swapping models when RAG answers went bad. Most RAG failures are retrieval failures, not generation failures. Chunking and ranking matter more than the model.` — adapted from `:1819`; first-person stance added, no numbers.
6. **Capability-as-risk** — "If it can [capability], it can [bad outcome]."
   `Any agent with tool access is an attack surface. If it can read the web and call APIs, it can be told to do something you did not plan.` — `:1826` (verbatim).
7. **Definitional reframe** — "[X] is a [small thing], not a [status thing]."
   `A thin wrapper on an API is a feature, not a company. The defensible part is always the workflow and the data.` — `:1821` (verbatim, trailing "the" dropped).
8. **Measurement jab** — "If you cannot [measure], you cannot [ship]."
   `If you cannot measure it, you cannot ship it. Most AI teams still have no eval set and one very confident founder.` — `:1823` (verbatim).
9. **Forgiveness contrast** — "Users forgive [minor]. They do not forgive [costly]."
   `Users forgive a wrong autocomplete. They do not forgive a spinner on every keystroke.` — adapted from `:1824`; bank's "three-second" number dropped.
10. **Reliability over score** — "[Operational property] matters more than [status metric] once [condition]."
    `Endpoint reliability and error rates matter more than leaderboard scores once a feature is in production.` — `:1054` (verbatim, Engineering Briefs).

Rotation rule: do not open two consecutive posts with the same skeleton. Current output fails this catastrophically — `Paying Silicon Valley rent...AI hallucinate a Python loop` recurs across the 74 failed drafts.

---

## 6. Three before/after rewrites

"Before" is verbatim stored text (cut marker where truncated). "After" contains **no invented number**, states one idea, opens in first person, and ends with a specific answerable question.

### Rewrite A — failed draft, invented numbers removed

- **Before** (`original_post`, failed, topic `Frontier Reasoning Drift & Cost per 1M Tokens (DeepSeek vs Claude vs Gemini)`):
  `Paying $50 to watch an AI overthink a bug for 10 minutes just to suggest \`npm install left-pad\`. Truly we are living in [cut@120]`
- **Why it fails:** `$50` and `10 minutes` are unsourced; the joke is the whole post; no mechanism; no reader action. Source context available: `Latency and cost diverge sharply once long-horizon coding tasks are measured end to end instead of per-token.` (`src/trend_hunter.py:1030`).
- **After:**
  `I stopped comparing models per token. On long coding tasks, cost and latency diverge once you measure the whole loop end to end, not the answer. What does your trace show?`

### Rewrite B — shipped off-niche/finance-adjacent roast → on-niche

- **Before** (`original_post`, success, target `The AI bubble and pitch deck madness`):
  `Bro really slapped a $2 ChatGPT wrapper on an Excel sheet and named it "Quantum Neural Enterprise Synergy" for a $20M va [cut@120]`
- **Why it fails:** `$2` and `$20M` are unsourced; "Bro really..." is a roast register, not a builder's position. The on-niche bank claim exists: `A thin wrapper on an API is a feature, not a company. The defensible part is always the workflow and the data.` (`src/trend_hunter.py:1821`).
- **After:**
  `I'll say it plainly: a thin wrapper on an API is a feature, not a company. The defensible part is the workflow and the data you own. Which part of your stack is actually yours?`

### Rewrite C — shipped sport post → benchmark reality

- **Before** (`original_post`, success, target `mexico vs jamaica`):
  `Watching Mexico vs Jamaica is basically a stress-test for my heart rate while pretending I understand tactical football.`
- **Why it fails:** zero AI content; "my heart rate" is incidental first-person, not a stake. Replace with the on-niche bank claim at `src/trend_hunter.py:1813`.
- **After:**
  `I've stopped trusting the chart. A model can win every public benchmark and still feel slow in production, because p95 latency and queueing are not on the leaderboard. What does your trace say?`

---

## 7. Scoring rubric (proposed, 0–10 — these are editorial thresholds, not measured data)

| Dimension | Points | Pass condition | Instant fail (0) |
|---|---|---|---|
| Niche fidelity | 0–2 | Topic is AI engineering / LLM benchmarks / dev tools / builder culture (`agents/README-X-BLUESKY.md:13`) | Sport, cinema, finance, politics, celebrity; any brand or URL (`:11`) |
| Evidence integrity | 0–2 | Every number appears in supplied topic context; else no number | Any unsourced number, fake credential, fake telemetry (`:12`) |
| First-person stake | 0–2 | First line is first person with a real consequence or position the reader can dispute | No author; "Bro..." roast; incidental "my" joke |
| One idea + specificity | 0–2 | One claim, one named mechanism, one concrete detail from context | Two ideas, vague industry commentary, recycled template |
| Hook + replyable end | 0–1 | Claim-first open; ends with one specific answerable question or clear counter-position | Question-open, "thoughts?", "what do you think", "agree?" |
| Format | 0–1 | ≤240 chars, ≤1 natural hashtag, no links, no leading emoji | Over length, hashtag stuffing, link |

**Publish threshold: ≥8/10 AND no zero on niche fidelity or evidence integrity.**
Known consequences if adopted: the 74 failed drafts score 0 on evidence integrity (invented numbers) and 0 on one-idea (template repetition); the 20 shipped off-niche posts score 0 on niche fidelity; Rewrite A/B/C score 10/10 against this rubric. **The gate would currently reject almost everything** — that is the point, but see the failure modes in §9.

---

## 8. What I could NOT verify (explicit)

1. **Engagement outcomes.** `trial_metrics.json` event fields are exactly `timestamp, action_type, status, is_dry_run, target, content_preview, reason, duration_s`. No likes, replies, reposts, quotes, impressions, or follow counts. Every "engagement" claim in this file is mechanism inference, not a measured result. `agents/README-X-BLUESKY.md:26` confirms: "No outcome measurement on either platform."
2. **Post endings and actual length.** `content_preview` is truncated to 120 chars (`src/x_state.py:188`, `:227`). "Ends with something replyable" and the ≤240-char rule are **insufficient evidence** from previews. My 0/97 "thoughts?" count is therefore meaningless as a measure of endings — it only covers the first 120 chars.
3. **Which drafts truly shipped.** 74 of 97 content-bearing drafts are `status="failed"` with a Playwright error; they carry generated text but did not publish. Only 23 are `success`. Voice statistics over all 97 describe *drafts*, not the live feed. `status="success"` itself is only "the post call returned success," not "it was seen."
4. **Exact invented-number count.** Digit/unit regexes are reproducible (38/74, 27/74) but miss spelled-out quantities ("four business days", "three hours", "half my salary"), and I will not guess a single exact figure. Insufficient evidence.
5. **Reproduction of "43%" and "51/177".** Not reproducible from the current file; see §2. The 51/177 string is traceable to `research/linkedin-voice-findings.md:14`, not to a fresh count here.
6. **Root cause of off-niche supply.** Strongly indicated by `scheduler.py:1275-1278`, `:1307`, `trend_hunter.py:1783-1787`, `:1284-1294` and `ai_generator.py:10`, but no telemetry logs which bank call produced each shipped post. The targets are consistent with this chain; it is not proven by a log line.
7. **Bluesky.** Not analysed here. No claims made about Bluesky voice or hooks.

---

## 9. Recommendations, ranked by impact × ease — and why each might fail

**1. Add an X-specific pre-publish gate: ban unsourced numbers, question-first openers, and banned openers; reuse `validate_no_number_without_source` / `validate_no_banned_openers` from `src/growth.py:227-249`.** Impact high, ease medium.
*Strongest reason it might fail:* the gate throws posts away instead of repairing them (`src/growth.py:302-304`: "Never silently edits numbers... Callers must regenerate once and then skip"). Casual/unfiltered topic contexts are single sentences with no numbers, so any numeric claim is auto-rejected; combined with the existing 74 skipped events, X volume could fall below the 4/day cap and the account could go quiet. If reach is driven by volume, this loses before it wins — and we cannot test that, because there is no engagement data (§8.1).

**2. Remove the off-niche fallback for X and narrow `X_UNHINGED_SYSTEM_PROMPT:10` to the builder's lens only** (delete "You also comment on wider internet culture"). Impact very high, ease low–medium.
*Strongest reason it might fail:* the sport/roast posts are the only ones that shipped in this window (23 success vs 74 failed). If those roasts are in fact what drives follows, removing them removes the only content that reaches the feed. Also, `get_x_growth_topics()` has 24 topics (`src/trend_hunter.py:1811-1836`) and `posted_history` dedup (`src/scheduler.py:1293-1297`) will exhaust them; the result could be more skips and more cannibalization, not a cleaner niche.

**3. Put a first-person, one-idea rule into `generate_hot_take` (`src/ai_generator.py:194-211`) and rotate the 10 hooks in §5; explicitly ban the "Paying [rent] to watch AI hallucinate..." skeleton.** Impact high, ease medium.
*Strongest reason it might fail:* first-person becomes decorative. The 5 shipped first-person hits are already incidental ("we cooked", "my heart rate"), and "I stopped..." can become the next template in four posts. Without a source-grounded detail from the topic context, a first-person opener is just a costume over the same roast.

**Not recommended (costs more than it returns here):** re-tuning hashtags or emoji. Shipped previews show 1/97 hashtag and no "thoughts?" bait in the visible text; there is no evidence these are the bottleneck, and no telemetry to prove a lift.

**Out of my remit but load-bearing:** 74 of 97 drafts died on a missing Playwright browser (`BrowserType.launch: Executable doesn't exist...`), so 76% of the "voice" sample never shipped. `agents/README-X-BLUESKY.md:22` says this is "fixed in cloud." Until that is confirmed with a fresh trial file, any voice change is being measured against a feed whose dominant sample is sport roasts, not the AI drafts the generator spends its effort on.
