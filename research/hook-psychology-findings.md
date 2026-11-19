# Hook & comment psychology findings — LinkedIn creator account (2026)

Scope: one creator account (AI engineering / LLM benchmarks / dev tools), 1 LinkedIn post/day, no brand mentions, no outbound links in post bodies, no invented statistics, no "What is X?" or "Understanding the real-world mechanics of X" openers, no "thoughts?" endings.

Goal: turn these mechanics into checks the generator can run, rather than advice a human has to remember.

## Evidence key

- **[P]** Platform-adjacent data: LinkedIn staff statements or large third-party post datasets.
- **[A]** Peer-reviewed attention/curiosity research.
- **[I]** Our inference from [P]+[A] for this specific account. Test it; do not quote it as a platform fact.

Sources (all retrieved 2026-11-20):

1. [Buffer, "How LinkedIn's Algorithm Works in 2026, According to the LinkedIn Team" (19 Dec 2025)](https://buffer.com/resources/linkedin-algorithm/) — summary of LinkedIn staff interviews (Dan Roth, Alice Xiong, Laura Lorenzetti). Ranking inputs described as Relevance, Expertise, Engagement; "meaningful comments from people who typically interact with this topic"; connections see posts first; knowledge-rich posts get extended reach; avoid engagement bait; "three or fewer" hashtags; hook advice ("What's the most interesting part of your post? Put it at the top"); links in comments "does not appear to have a negative impact"; replying to comments correlated with +30% engagement across 72,000 posts; carousels ≈6x text-only engagement across >1M posts.
2. [Buffer, "The Best Time to Post on LinkedIn in 2026: 4.8 Million Posts Analyzed" (9 Sep 2026)](https://buffer.com/resources/best-time-to-post-on-linkedin/) — peak window 3–8pm weekdays, Wednesday 4pm top slot; explicitly notes LinkedIn has **not** confirmed an official 60/90-minute "golden hour".
3. [Sprout Social, "Best times to post on LinkedIn in 2026" (31 Mar 2026)](https://sproutsocial.com/insights/best-times-to-post-on-linkedin/) — ~2B engagements across 307,000 profiles (27 Nov 2025–27 Feb 2026); Tue 11am–5pm, Wed 11am–4pm, Thu 1–5pm; tech/software Tue–Wed 10am–4pm; weekends worst. **Conflicts with source 2 on evening vs midday.**
4. Loewenstein, G. (1994), "The psychology of curiosity: a review and reinterpretation", *Psychological Bulletin* 116(1), 75–98, [doi:10.1037/0033-2909.116.1.75](https://doi.org/10.1037/0033-2909.116.1.75) — curiosity is triggered by a felt information gap; the gap must be specific and closable.
5. Kang, M.J. et al. (2009), "The wick in the candle of learning: epistemic curiosity activates reward circuitry and enhances memory", *Psychological Science* 20(8), 963–973, [doi:10.1111/j.1467-9280.2009.02402.x](https://doi.org/10.1111/j.1467-9280.2009.02402.x) — curiosity improves retention of the answer. Supports building a reference object, not a tease.
6. Berlyne (1960), *Conflict, arousal, and curiosity*, McGraw-Hill; summarized in [Wikipedia, "Curiosity"](https://en.wikipedia.org/wiki/Curiosity) (accessed 2026-11-20) — novelty, uncertainty, incongruity and surprise are the reliable curiosity triggers.
7. Ghibellini & Meier (2025), "Interruption, recall and resumption: a meta-analysis of the Zeigarnik and Ovsiankina effects", *Humanities and Social Sciences Communications* 12(1), [doi:10.1057/s41599-025-05000-w](https://doi.org/10.1057/s41599-025-05000-w); summarized in [Wikipedia, "Zeigarnik effect"](https://en.wikipedia.org/wiki/Zeigarnik_effect) — **no** memory advantage for unfinished tasks; a reliable tendency to *resume* them. Open loops help people respond, not remember, and must never be used to withhold the answer.

## What actually drives comments, saves and follows here

- **Comments:** LinkedIn staff describe engagement as "meaningful comments from people who typically interact with this topic", and explicitly deprioritise raw virality and engagement bait [1]. So the unit is *one substantive reason to reply*, not a volume ask.
- **Saves:** no public evidence that the Save button is a weighted ranking input. What is documented is that knowledge-rich, expertise-demonstrating posts get extended distribution [1], and that curiosity around a closable gap improves retention of the answer [4][5]. We treat saves as the behavioural proxy for "reference value" and build for that; we do **not** claim a save multiplier.
- **Follows:** relevance + expertise are ranking inputs, and a niche lets the system match the right audience [1]. Follows come from being clearly *this kind of account*, not from a CTA.
- **Format:** carousels strongly outperform text-only in Buffer's dataset [1], but that is a format correlation, not proof of any specific slide technique.
- **Replies:** replying to your own commenters correlates with +30% engagement (72,000 posts) [1]. Correlation, not a guaranteed lift.

## Ranked enforceable rules

Ranked by expected engagement gain per unit of effort, using: strength of cited evidence × how directly the generator controls it ÷ implementation cost. Bands are qualitative by design; no invented gain percentages.

| Rank | Rule | Gain/effort | Confidence |
|---:|---|---|---|
| 0 | Hard ban sweep (gate) | very high | [P] |
| 1 | Consequence-first first line | very high | [P][A] |
| 2 | One-line-answer ending | high | [P][I] |
| 3 | First comment = new value, link-free | high | [P][I] |
| 4 | One falsifiable position per post | high | [P][A] |
| 5 | Resolvable curiosity gap, never withheld | medium-high | [A] |
| 6 | Save-able artifact + mobile formatting | medium-high | [P][A] |
| 7 | Carousel pacing | medium | [P][I] |
| 8 | Reply-window posting slot | medium-low | [P] |
| 9 | ≤3 hashtags | low-medium | [P] |
| 10 | "See more" budget on the first two lines | low | [I] |

### Rank 0 — Hard ban sweep (gate, not a tactic)

**Rule.** Reject any generated string containing: `http://`, `https://`, `www.`, any brand/domain token, `thoughts?`, `what do you think`, `comment below`, `drop your thoughts`, `Understanding the real-world mechanics of`, `What is ` as an opener, `In today's`, `let's dive in`, `game changer`, `unlock`, `the future of`, `I spent` (carousel hooks).

**Enforcement.** Case-insensitive regex over `post_text`, `cover.*`, `slides.*`, `first_comment`, `cta.*`, `alt_text` before publication. A numeric token in the post must exist verbatim in the supplied `context`; otherwise strip it (no invented statistics).

**Why.** Engagement bait and spam CTAs hurt reach [1]/[1 FAQ]; links out of the body are banned for this account.

### Rank 1 — Consequence-first first line

**Rule.** The first line is a declarative statement that names a specific mechanism and a consequence for the reader. No preamble, no definition, no question.

**Enforcement.** Let `L = post_text.split("\n")[0]`:
- `len(L)` between 60 and 160 characters (our preview budget, not a LinkedIn claim).
- `L` contains ≥1 topic anchor (a token from the supplied topic/context, e.g. `KV cache`, `io_uring`, `p99`, `fan-out`).
- `L` contains ≥1 consequence marker from: `costs`, `doubles`, `drops`, `fails`, `silently`, `latency`, `memory`, `accuracy`, `wins`, `loses`, `breaks`, `starves`, `tax`, `saves`, `wrong`, `slower`, `faster`.
- `not L.rstrip().endswith("?")` and `not re.match(banned_openers, L)`.
- No digit in `L` unless that digit appears in `context`.

**Why.** LinkedIn's own staff advice: put the most interesting part at the top and tell the payoff before the setup; "pack as much value as possible into those crucial first few seconds" [1]. Novelty, uncertainty and incongruity are the reliable curiosity triggers [6]. This single check fixes the current generic-explainer failure mode, because "Understanding X…" and "What is X?" both fail the consequence + anchor test.

### Rank 2 — One-line-answer ending

**Rule.** The post ends with exactly one question answerable in ≤12 spoken words, about the mechanism named in the hook. Never "thoughts?", never a multi-part question, never "comment to get X".

**Enforcement.**
- Last non-empty content line: `<= 120` chars, ends with `?` or matches `^(Pick|Name|One word|One number)`.
- `len(re.findall(r"\?", post_text)) == 1` (one question mark in the whole post body).
- Shares ≥1 topic anchor with line 1.
- Banned in the ending: `thoughts`, `what do you think`, `agree?`, `let me know`, `comment`, `DM`, `follow for`.

**Why.** LinkedIn staff recommend CTAs that invite real conversation while penalising bait [1]. A binary or single-value request minimises the effort of replying, which is the scarce resource on a professional feed [I].

### Rank 3 — First comment = new value, link-free

**Rule.** The first comment adds one engineering detail absent from the body, then asks one narrower follow-up. It is not a link slot, a resource tease, or a repeat of the body's question.

**Enforcement.** See the full spec below. Hard cap 350 chars (matches the existing clamp), no URLs/domains/brands/numbers not in context, exactly one `?`.

**Why.** LinkedIn staff say links in comments don't appear to hurt performance [1], but this account bans all outbound links, so the comment must carry its own value. A seeded, substantive first comment gives the first organic reply something to answer [I]. Replying to those replies correlates with higher engagement [1].

### Rank 4 — One falsifiable position per post

**Rule.** The post takes exactly one debatable stance tied to the named mechanism. No fence-sitting in the hook or stance sentence.

**Enforcement.** First 3 lines must contain ≥1 stance marker: `wrong default`, `overrated`, `underrated`, `the mistake is`, `I would not`, `stop`, `should`, `is not`, `beats`, `loses to`, `most teams`. The stance sentence must not contain `it depends`, `both have merits`, `in some cases`, `varies`.

**Why.** "Expertise" and "meaningful comments" are ranking inputs [1]; a position gives a reader something specific to agree or disagree with, and disagreement is a comment [A][I]. Existing X generator already enforces "take a position" — port it to LinkedIn.

### Rank 5 — Resolvable curiosity gap, never withheld

**Rule.** The hook opens a specific gap; the body closes it inside the first 3 lines after the hook. The answer must be in the post, never "comment to find out".

**Enforcement.** First 3 lines after the hook must contain ≥1 gap marker (`why`, `but`, `except`, `until`, `the part that`, `what breaks`, `failure mode`, `cost`) and ≥1 resolution marker (the named consequence from Rule 1, or `because`, `the cause is`, `it turns out`, `here is the rule`). If the post's only resolution is in `first_comment`, reject.

**Why.** Information-gap theory: the gap must be concrete and closable to drive attention [4]; curiosity aids memory of the answer [5]. Withholding the answer for comments is bait, has no memory benefit, and the 2025 meta-analysis shows open loops support *resumption*, not recall [7].

### Rank 6 — Save-able artifact + mobile formatting

**Rule.** Every post contains one reusable object: a 3–5 item checklist, a decision rule, or a vertical scorecard, plus a one-line "use this when" statement.

**Enforcement.**
- Regex for a 3–5 item numbered/bulleted block, or 3+ `•`/`▼` scorecard rows.
- A line containing `use this when`, `rule of thumb`, `default to`, or `if ... then ...`.
- No line >40 chars in diagram/scorecard blocks; no `+---+`, no `| col |`, no horizontal `─►` chains (already enforced in `generate_linkedin_take`).

**Why.** Knowledge-rich content gets extended distribution [1], and curiosity improves retention of useful answers [5]. Formatting for mobile is explicitly recommended [1]. Keep the artifact in text even on text-only days, since Sprout reports 51% of users prefer text-based posts [3] — do not force a carousel just to get a checklist.

### Rank 7 — Carousel pacing

**Rule.** Cover subhead states the reader's consequence (already enforced); every slide title is a claim, not a label; every slide takeaway is a standalone sentence that survives being screenshotted.

**Enforcement.** For each slide: `title` must contain a verb or stance marker (not just a noun phrase, e.g. reject "KV Cache", accept "KV cache is a memory tax"); `takeaway` must be a complete sentence with a period, ≤120 chars; `cover.subhead` must contain a consequence marker from Rule 1.

**Why.** Buffer's >1M-post dataset shows carousels ≈6x text-only engagement [1]. This is a format-level correlation; the pacing checks are our leverage on that format [I]. One point per slide is already enforced.

### Rank 8 — Reply-window posting slot

**Rule.** Schedule the daily post in a weekday slot where the account can reply to comments for the following 60–90 minutes. Treat universal "best time" tables as tie-breakers only.

**Enforcement.** Scheduler rejects weekend slots; prefers Tue/Wed/Thu 10am–4pm in the audience's local time (Sprout [3], including tech/software) **or** Wed/Fri 3–4pm (Buffer [2]) — because the datasets conflict, alternate by week and read our own analytics. Do not claim a confirmed "golden hour": LinkedIn has not confirmed one [2].

**Why.** Early interaction helps, but the exact window is unconfirmed [2]; availability to reply is the part we control, and replying correlates with +30% engagement [1].

### Rank 9 — ≤3 hashtags

**Rule.** 3 hashtags maximum: 1 broad, 2 topic-specific.

**Enforcement.** `len(hashtags) <= 3`; reject generic-only sets (`#Tech`, `#Business`); rotate the two specific tags across posts.

**Why.** LinkedIn staff: hashtags are "a nice to have, not a need to have", "don't use too many" [1]. Note: `append_hashtags()` currently defaults to 5 tags for two LinkedIn generators — see conflicts below.

### Rank 10 — "See more" budget on the first two lines

**Rule.** Put the entire hook and its payoff inside the first two short lines, each ≤90 chars, separated by a blank line.

**Enforcement.** `len(post_text.split("\n\n")[0]) <= 200` chars and the first block contains both the anchor and the consequence from Rule 1.

**Why.** This is our conservative preview budget so the claim survives mobile truncation [I], not a claim about LinkedIn's exact truncation point. It is cheap to enforce and protects the work done by Rule 1.

## Five comment-trigger endings

All avoids "thoughts?", "what do you think?", multi-part questions and bait. Each is answerable in one word/number.

1. **Binary cut** — "KV cache or context window: which do you cut first when memory gets tight? One word."  
   *Why:* two familiar nouns, one decision. *Reject if* both options are not already in the post.
2. **Single number** — "What p99 budget does your team actually enforce on this path? One number."  
   *Why:* engineers carry this number; near-zero typing cost. *Reject if* the topic is not latency-related — swap in the topic's metric (fan-out, retries, batch size).
3. **Name your default** — "Timeout here: retry or fail fast? Just your default."  
   *Why:* asks for a habit, not an argument; defaults are easy to report. *Reject if* the post never mentioned timeouts.
4. **One-word failure mode** — "When you shipped this, what broke first: memory, latency, or correctness? One word."  
   *Why:* invites a war story disguised as a one-word answer; the story follows in replies. *Reject if* the three options don't map to the post's mechanism.
5. **Under-rated metric** — "Which is most under-measured in your benchmarks: tail latency, cold starts, or cache hits? One word."  
   *Why:* opinionated and rankable; each choice implies a reason. *Reject if* none of the three appear in the post.

Shared check: exactly one `?` in the post, ending ≤120 chars, shares a topic anchor with line 1. Rotate these five across posts; the same structure twice in a row reads as a template (the carousel generator already dedupes recent hooks).

## First-comment spec (link-free post)

**What it adds.** One *new* self-contained engineering detail the body did not have room for (a concrete failure mode, a decision rule, or a one-line implementation tip), followed by one narrower follow-up question. It must be useful if the post is never opened again, and it must not repeat the post's closing question verbatim. No link, no "tracker in comments", no "DM me", no "comment to get", no brand, no statistic that is not in the supplied context.

**Length and shape.** 180–320 characters; hard cap 350 (matches `_clamp_text(..., 350)`). Two sentences: one value sentence ≤180 chars, one question ≤100 chars. Exactly one `?`. Plain text, no emoji bullets, no markdown. If it cannot fit, drop the question before dropping the value.

**Template.**

```
[One mechanism + its consequence, stated as fact]. [Narrow one-line question about the exact step or trade-off].
```

**Worked example (KV cache topic).**

> One detail the post skips: the cache grows with sequence length even when request rate is flat, so a traffic spike is not the only way to exhaust it. If you cap it, do you cap per request or globally? One word.

(≈240 chars, zero links, zero numbers, one question, adds a fact absent from the body.)

**When it is posted.** Immediately after the post is published. The current browser path already posts it about 10 seconds after publish (6s + 2s + 1s + 3s waits in `linkedin_automater.py`); keep that. Do not add a delay: there is no source showing a delay helps, and the scheduler warns LinkedIn may skip the first comment on personal tokens. Therefore the **post body must never depend on the first comment being visible** — no "see first comment" instruction anywhere.

**Aftercare.** Reply to every comment for the first 60–90 minutes. Buffer's 72k-post analysis found replying correlates with +30% engagement [1]; the "golden hour" itself is not LinkedIn-confirmed [2]. Never let the first comment become a resource tease now that all links are gone.

## Conflicts in current generator copy (for the implementing agent)

These are strings/prompts, not production changes made here:

- `ai_generator.py:464` CTA example "Drop your thoughts below — and check the first comment for the interactive benchmark tracker!" violates the "thoughts?" ban and promises a resource that no longer exists. Replace with Rule 2 ending.
- `ai_generator.py:373` "The interactive benchmark tracker is mentioned for the first comment" is stale under the no-links policy. Replace with "the first comment adds one self-contained tip, no links".
- `ai_generator.py:741` fallback opener "Understanding the real-world mechanics of …" is on the hard-ban list. Replace with a consequence-first fallback (Rule 1).
- `ai_generator.py:429` example hook "I spent 40+ hours benchmarking 260+ models…" contains invented statistics and conflicts with the carousel rule "Do not open with 'I spent'". Remove or make non-numeric.
- `ai_generator.py:1119–1124` first-comment prompt asks for an "open question asking developers how they handle this in production"; too broad for a one-line answer. Replace with Rank 3 + the spec above.
- `append_hashtags()` defaults to 5 tags for two LinkedIn generators; LinkedIn staff recommend three or fewer [1]. Lower the defaults.

## Evidence limits

- Sources 1–3 are secondary aggregations or interviews, not a published LinkedIn ranking specification. Treat them as directional.
- The posting-time datasets directly contradict each other (evening [2] vs midday [3]). A/B test on our own analytics; do not present either as fact.
- The +30% (replying) and ≈6x (carousels) figures are correlations from Buffer's datasets, not causal guarantees.
- No sourced number may be inserted into post copy unless the topic/context supplied to the generator contains it. The statistics in this document govern our rules only.
- The Zeigarnik "unfinished tasks are remembered better" claim is not supported by the 2025 meta-analysis [7]; open loops are used here only to prompt a response.

## Single highest-ROI mechanic

**Make the first line a consequence with a specific anchor, and reject every opener that is a definition, a question, or a preamble.** It is the gate on every other signal — if the thumb does not stop, the strongest ending and the best first comment are never seen — it directly removes the generic-explainer failure mode, it is backed by both LinkedIn staff hook advice [1] and curiosity research [4][6], and it costs one prompt line plus one regex to enforce.
