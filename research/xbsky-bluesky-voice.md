# Bluesky voice & hooks — evidence report

**Role:** Bluesky-native technical writer / growth operator (per `agents/bluesky-voice-and-hooks.md`).
**Scope:** shipped Bluesky text + current generation path only. Production code was **not** modified.
**Method:** parsed `trial_metrics.json` → `recent_events` (500 events), filtered `action_type == "bluesky_post"`, and counted the literal `content_preview` strings. Code claims cite `src/ai_generator.py` and `src/scheduler.py` as shipped. Counts below are reproducible from the JSON; classifications that require judgment are labelled *interpretive*.

---

## 0. What I could NOT verify (read this before trusting any number)

This is the honesty boundary. I made **no live Bluesky API calls** and had no credentials.

1. **Every usable preview is truncated.** 102/102 non-empty `content_preview` strings are **exactly 120 characters** — `src/tracker.py:177` stores `content_preview[:120]`. I therefore **cannot see the end of any shipped post**. Consequence: I cannot verify whether any post ends with a replyable question, how many hashtags it actually carries, its true length, or whether the "one concrete consequence" promised by the prompt landed. My question/tag counts below are *lower bounds on what is visible*, not measurements of the full posts.
2. **No full-text recovery locally.** `post_history.json` → `platform_history.bluesky.completed` contains only `post:<sha256>` hashes, no bodies. There is no Bluesky body archive in the repo.
3. **No outcome data at all.** `trial_metrics.json` records status/duration/target/preview/reason only — no likes, replies, reposts, impressions, or follows anywhere in the schema. "Engagement unmeasured" (charter) is confirmed: the measurement does not exist, so I cannot rank hooks by observed engagement.
4. **Numeric claims are unverified.** Figures appearing in shipped text — `40% variance`, `260+ models`, `25k+ logs`, `385x`, `320B`, `$1B`, `$12M`, `40% of search traffic`, `macOS 27.3`, `90 days` — are treated as *shipped strings*, not as verified facts. I could not confirm their provenance. I do not repeat any of them as fact in my proposed rewrites unless the number is present in the source `target` string, and I flag even those.
5. **Cannot attribute a post to a generator path from the data.** `src/scheduler.py:1494-1514` alternates between `generate_bluesky_concept_post` and `generate_bluesky_take` by `bsky_cycle` parity, but no per-event field records which path ran. Effects of the two prompts cannot be separated empirically here.
6. **Reply workflow output: none to judge.** There is exactly **1** `bluesky-replies` event; its status is `skipped`, reason `"Total daily limit reached (25/20)."`, preview empty. There are **0** `bluesky_reply` events. The new step has not produced a reply, so nothing can be said about reply voice quality.
7. **Git history unavailable** (`git` not installed in this environment), so I could not confirm the timing or diff of the "recent rewrite." I judged the **current code only**, as instructed.

---

## 1. Counts from actual shipped strings

### 1.1 Volume & status (`bluesky_post`, n=130)

| Measure | Count | Note |
|---|---:|---|
| `bluesky_post` events | 130 | all of recent_events for this platform |
| `status: success` | 101 | |
| `status: failed` | 1 | target: JVT / pixel-space video diffusion |
| `status: skipped` | 28 | preview empty in all 28 |
| non-empty previews | 102 | = 101 success + 1 failed |

**Correction to the brief:** "102/130 posts succeeded" conflates two numbers. **101** succeeded; **102** is the number of posts that had content at all (101 success + 1 failed). Actual rates: **101/130 = 77.7%** of scheduled slots, **101/102 = 99.0%** of attempted-with-content. The binding constraint is skips (28), not generation failures.

### 1.2 Hook-observable markers in the visible 120 chars (n=102)

| Marker | Count | Interpretation |
|---|---:|---|
| exactly 120 chars | 102 | all truncated (hard limit on analysis) |
| contains `?` | **2** | Both are *mid-post* question hooks, not confirmed endings: #39 "Bypassing pretrained autoencoders for raw pixel-space video diffusion? JVT uses…" (the one failed post) and #101 "Multimodal tabular learning bottlenecked by high-dim text/image embeddings? LightTAR replaces…". |
| ends with a replyable question | **0 confirmed** | Unobservable, not "zero exist." The prompt asks for one (`src/ai_generator.py:311`). |
| contains `#tag` | **0** | Tags would sit at the end → invisible. Unobservable, not "zero exist." |
| over-stuffed with tags (>2) | **0 confirmed** | Not observable. Note `generate_bluesky_take` relies on prompt-only "at most two technical hashtags" (`:313`); only `generate_bluesky_concept_post` enforces a cap in code via `append_hashtags(..., max_len=285)` (`:406`). |
| mentions "NeuBench" in body | **4** | #7, #12, #28, #84. Direct tension with "no brand" in the charter and "no brand promotion" in the system prompt (`:36`). |
| contains any digit in first 120 | **20** | Includes model names/versions and source numbers; provenance unverified. |

### 1.3 Opener classification — *interpretive*

Criteria used: **mechanism** = first sentence states a causal behaviour, failure mode, trade-off, or definition of a system (e.g. "Autoregressive decoding without KV caching is re-solving every prior step…" #6); **summary** = first sentence reports an event, launch, funding round, or telemetry headline rather than explaining a mechanism.

| Class | Count | Evidence |
|---|---:|---|
| mechanism / failure / definition opener | **93** | e.g. #1, #3, #4, #6, #9, #14, #19, #40, #64, #78, #94 |
| news / announcement / telemetry-summary opener | **9** | listed below |

The 9 *summary* openers (exact visible text): #12 "NeuBench speed testing reveals up to 40% variance…", #28 "NeuBench telemetry on 260+ models shows…", #47 "Zoox routing AV telemetry through Uber's dispatch layer…", #56 "macOS 27.3 brings granular permission boundaries…", #62 "A $1B valuation in 90 days for an AI security startup highlights…", #73 "A $12M raise for a domain-specific travel LLM agent…", #76 "Proton's Lumo desktop app brings…", #81 "AI summaries eating 40% of search traffic shifts…", #99 "Public market entry fundamentally shifts AI lab incentives…".

"Reads like a press release" — conservative, also interpretive: **at least 5** (#56, #62, #73, #76, #99) lead on a launch/valuation with evaluative adjectives ("massive demand", "Interesting step", "Necessary hardening").

**Counter-argument to this whole section:** a news-driven technical account legitimately leads with news, and "press release" is a tone judgment, not a measurable property. Reasonable coders would move several of the 9 into *mechanism*. Treat 93/9 as an estimate with an auditable item list, not a precise fact.

### 1.4 Repetition (from shipped `target` field)

| Topic | Posts |
|---|---:|
| "What is a Logit?" variants | **12** |
| Vector Embeddings variants | 4 |
| KV Cache variants | 3 |
| "LLM API Outage Frequency & Degradation Index" | 3 (exact duplicate target) |
| EgoX | 3 (exact duplicate target) |
| distinct target titles | 93 / 102 (9 exact repeats beyond first) |

The same concept is re-explained 12 times in 102 posts. That is a hook problem as much as a topic problem: the twelfth "Logits are raw model scores…" cannot earn attention the way the first did.

---

## 2. Code reality vs the brief

- `src/ai_generator.py:32-37` — `BLUESKY_SYSTEM_PROMPT` is **not** a sharp creator voice. It says "Professional, collegial, technically rigorous," "under 280 characters," "at most two technical tags." The sharper instructions live in the **per-call prompt** of `generate_bluesky_take`: `:308` "Lead with the mechanism or trade-off, not a summary of the headline" and `:311` "End with a short question or a testable claim that invites replies." Judge both as shipped.
- `src/ai_generator.py:319-333` — `generate_bluesky_sniper_reply` explicitly instructs "Do NOT sound casual or snarky. Maintain high technical standards." The reply voice is deliberately conservative; a sharp-creator repositioning will not reach replies without editing this.
- Length spec is inconsistent across the codebase: `:36` and `:309` say **280**, `:400` says **240**, `append_hashtags` uses **285** (`src/ai_generator.py:406`), and the role brief says **under 300**. Pick one.
- `src/scheduler.py:1552-1553` sets `media_path = None` unconditionally — every published Bluesky post is text-only, so no visual can rescue a weak hook.

---

## 3. Bluesky engagement spec (proposed)

One post: **under 300 chars** (single canonical limit), **one insight**, **one concrete consequence** (latency / cost / memory / reliability / eval quality), **one question or testable claim**, **at most two tags**, **no links, no brand**. First 120 chars must stand alone as a complete thought — that is the only part the current telemetry keeps, and it is also the only part a scroller reliably reads. Open on the mechanism or the failure mode, never on "X raises $Y."

**Counter-argument:** forcing a question into every post reads formulaic on AT Protocol, where a crisp contrarian claim often outperforms a question. Prefer "question **or** testable claim" (the shipped prompt already allows both); do not mandate a literal `?`.

---

## 4. Ten ready hook patterns (examples are **proposed** rewrites, not shipped posts)

All examples use topics present in the shipped `target` strings. No example invents a number.

1. **Failure-mode first** — "X fails when Y." *Example:* "KV-cache eviction fails exactly when long-context agents need it most: the hot prefix gets dropped mid-run. How are you pinning it?" (topic: KV cache)
2. **The hidden cost** — "The expensive part isn't X, it's Y." *Example:* "The cost in continuous batching isn't the matmul, it's the scheduler waiting on the longest sequence. Profile the queue, not the GPU." (topic: continuous batching)
3. **Myth → correction** — "X ≠ Y." *Example:* "Logits aren't probabilities. They're unbounded scores; Softmax is the only thing that makes them comparable. Seen pipelines skip that step?" (topic: logits)
4. **Imperative warning** — "Stop/Treat/Never…" *Example:* "Stop handing local coding agents raw cloud credentials. Scoped, short-lived tokens turn a prompt-injection hit into a contained incident." (topic: agent credentials)
5. **Mechanism in one line** — "X is Y doing Z." *Example:* "A tensor core is a block multiplier: it eats whole matrices per clock, not single scalar products. Misaligned dims waste those cycles." (topic: tensor cores)
6. **Counterintuitive consequence** — "A makes B worse." *Example:* "Cutting precision in video diffusion can increase total latency: more steps to recover quality erase the per-step win. Where's your break-even?" (topic: video diffusion)
7. **Analogy with a boundary** — "Think of X like Y — but Y breaks when Z." *Example:* "Think of the KV cache like a notebook you never erase. It's fast until context grows past memory, then the page-fault bill arrives." (topic: KV cache)
8. **Question-as-hook (diagnostic)** — "Why does X do Y?" *Example:* "Why do reasoning models drift on long tasks even when the final answer looks right? Worth reading the trace, not just the final score." (topic: reasoning drift)
9. **Testable claim / invitation to disagree** — "Claim: X." *Example:* "Claim: for small teams, a well-profiled single endpoint beats a seven-model router. Where's the clean head-to-head eval?" (topic: model routing; "seven models" from shipped target "Seven new models…")
10. **News → engineering consequence** — "The headline is X; the engineering problem is Y." *Example:* "The headline is a router launch. The engineering problem is eval discipline: seven models means seven chances to ship an unmeasured regression." (topic: model proliferation)

**Counter-argument:** patterns 4, 9 and 10 read as shepherding opinion, which the charter forbids only when it becomes bait or hype. Keep them evidence-led; cut any that a reader could mistake for a product pitch.

---

## 5. Three before/after rewrites

"Before" is the **verbatim 120-char shipped preview** (truncation included — that is the whole observable artifact). "After" is a proposed replacement, under 300 chars, no links, no brand, sourced only to the shipped `target`.

### 5.1 Definitional explainer (post #1 — also a repeated topic)

- **Before:** `Logits are raw model scores before normalization—like raw race times before grading. \n\nNever apply Softmax before cross-`
- **After:** "Logits are raw scores, not probabilities. Softmax is the grading curve that turns them into odds — skip it and your top-1 looks confident for the wrong reasons. Where have you seen that bug hide?"
- **Why:** complete thought inside 120 chars, one mechanism, one consequence, one answerable question, distinct framing from the other 11 logit posts.

### 5.2 Telemetry-summary opener (post #12)

- **Before:** `NeuBench speed testing reveals up to 40% variance in real-world token throughput across major hosted LLM APIs. Don't let`
- **After:** "Same model, same prompt, different hosted endpoint — and your tail latency moves. The number to watch isn't average throughput, it's variance. Are you measuring it?"
- **Why:** removes the brand self-reference (4 posts do this), leads with the consequence rather than "our testing reveals," and asks a question an engineer can answer. **No number is carried over** from the unverifiable `40%`.

### 5.3 Press-release opener (post #62)

- **Before:** `A $1B valuation in 90 days for an AI security startup highlights the massive demand for automated remediation. But veloc`
- **After:** "A security startup hit a billion-dollar valuation in about three months. The engineering question is less about the round than about the claim: can automated remediation actually be verified, or just generated? What would you trust as evidence?"
- **Why:** keeps the number **only** because it is in the shipped `target` ("$1B valuation in about 3 months" — I use "about three months" rather than the preview's derived "90 days"), drops "highlights the massive demand," and converts hype into a technical question.

**Counter-argument to all three:** the shipped previews are truncated, so the "after" may be rewriting a perfectly good ending I never saw. If the full posts already end with strong questions, these changes mostly reduce brand mentions and add topic variety — still useful, but smaller than claimed.

---

## 6. Recommendations, ranked by impact × ease — each with its strongest counter-argument

**R1 — Stop wasting the first 120 chars on headlines; enforce mechanism-first in the generation prompt.** Shipped evidence: 93/102 already do this (*interpretive*), so the gain is concentrated in the 9 summary openers and the 12 logit repeats. Cheap: prompt-level change already exists (`:308`) — make it a hard rule and add a post-generation check that the first sentence contains a causal verb. **Strongest counter-argument:** most posts already pass; this optimizes a small tail and a validator could flatten voice into template-speak.

**R2 — Instrument outcomes before changing more voice.** There is no engagement field anywhere in `trial_metrics.json`. Add `replies/likes/reposts` capture for `bluesky_post` events so hook variants can be compared. **Strongest counter-argument:** this costs engineering time and yields nothing for weeks; the charter's mandate is to ship aggressive changes now, and engagement may be trackable natively on Bluesky without repo changes.

**R3 — Break the repetition loop and the brand self-reference.** 12 logit posts, 4 embedding posts, 4 "NeuBench" mentions. Add "NeuBench" to the sanitizer's blocked terms for post bodies and raise topic-dedup weight in `src/scheduler.py:1465-1488`. **Strongest counter-argument:** "NeuBench telemetry" is the account's own measurement identity — removing it may reduce credibility rather than improve it, and the charter's "no brand" may be aimed at external brand promotion, not self-attribution.

**R4 — Reconcile the length spec (240 / 280 / 285 / 300) into one number.** Pure clarity fix. **Strongest counter-argument:** low impact on engagement; different platforms' internal caps were deliberate.

**R5 — Give the new reply workflow a test run before judging it.** Only one `bluesky-replies` event exists and it was skipped on a daily limit. **Strongest counter-argument:** the reply prompt (`:319-333`) is deliberately conservative; testing it as-is may just confirm a bland voice.

---

## Return (per charter)

**Top 3 findings**
1. **The measurement blind spot is total.** 102/102 shipped previews are truncated to 120 chars (`src/tracker.py:177`) and no engagement fields exist, so the central claim — "hooks are weak" — is currently **unfalsifiable** from local data. Only 2/102 show a question, and both are mid-post, not endings.
2. **The brief's success figure is mis-stated.** 101 posts succeeded, 1 failed, 28 were skipped — not "102 succeeded." The binding problem is skips, not failures.
3. **Repetition + brand leakage coexist with good mechanics.** 12 logit posts and 4 "NeuBench" body mentions in 102 posts; yet 93/102 open on a mechanism (*interpretive*) and the take prompt already asks for mechanism-first + a question.

**Strongest recommendation:** **R2 — instrument outcomes first.** Every voice change is a guess until `bluesky_post` events carry engagement data; this is the single change that converts all other recommendations from opinion into measurement. Counter-argument: it delays visible action and is a no-op for reach in the short term.

**Biggest uncertainty:** Whether the truncated half of each post contains the question, consequence, and tags the prompt demands. I **cannot** verify endings, tag counts, or true lengths from local data, and I made **no live API calls** — so any claim about "how many end with a replyable question" is explicitly a non-answer: **0 confirmed, not 0 observed as absent.**
