# X + Bluesky Synthesis — Manager's Call

Five agents audited X and Bluesky. I challenged their claims against the actual
code and shipped data. This file is the decision record; the reports are evidence.

## What survived scrutiny

1. **X off-niche content is far worse than I assumed.** 20 of 23 successful X
   posts had sport/politics/finance/meme targets (the X voice agent's 87% figure),
   not the 43% from an older baseline. The shipped voice sample is mostly failed
   retries; the witty first-person drafts never published.
2. **X replies are a no-op, not a threshold problem.** 35 skips each took
   193–197 s — browser discovery timeouts returning zero usable URLs. There is
   no engagement threshold in the code. 8 `unknown` reservations were permanent
   locks. The red team vetoed off-niche viral sniper replies outright.
3. **Bluesky replies were killed by the posting job's global cap**, not by a lack
   of targets (25/20 on the single attempt). Bluesky is the only healthy
   publisher and the only platform with free public per-post counts.
4. **The evidence gate had real holes**: `260+ models`, `385x`, `25k+ logs` were
   invisible to the regex; a fabricated "up to 40%" in a curated brief passed as
   "sourced"; brand stripping left lowercase clauses after full stops.
5. **Outcome data does not exist on either platform.** All `content_preview`
   strings are truncated at 120 chars, so claims about endings are unfalsifiable.
   `/api/stats` uses hardcoded/estimated numbers. Any "engagement went up" claim
   would be another invention.

## Decisions where agents disagreed

| Disagreement | Call |
|---|---|
| Distribution says instrument first; voice agents say ship changes now. | **Both.** Correctness (niche filter, gate, measurement log) ships now. Voice/hook changes are unverifiable until we have outcomes — they are not declared wins. |
| Reply engineer says retire X replies entirely; owner wants engagement anyhow. | **Keep them, but only on AI-engineering accounts, with a session check, stale-reservation pruning, and explicit skip logging.** If there is still no verified success after the next cycles, we kill the channel — I will not pretend a no-op is growth. |
| Bluesky agent wants deeper prompt work. | **One prompt edit only** (first person + consequence + short question). Further voice work waits for real outcome data. |
| Red team vetoes "viral sniper" replies. | **Accepted.** Off-niche roasts on a personal developer profile are a credibility liability, not growth. |

## Shipped in this pass

- `src/scheduler.py`: hard off-niche filter for X originals; growth bank as the
  only fallback; `_publish_gate()` wired into all 7 X/Bluesky publish and reply
  sites; stale unknown X reservations pruned; early X session check; AI-only
  reply targets; per-post outcome logs for X and Bluesky (null metrics).
- `src/growth.py`: numeric regex now catches `385x`, `260+ models`, `25k+ logs`;
  `evidence_gate()` hardening; capitalisation after stripped brand clauses.
- `src/trend_hunter.py`: removed fabricated stats from curated briefs/concepts.
- `src/ai_generator.py`: Bluesky prompt now requires first person, one
  mechanism, one consequence and one short answerable question.
- `.github/workflows/bluesky_engagement.yml`: new every-3-hour workflow in its
  own concurrency lane with all posting caps zeroed.
- `.github/workflows/x_automater.yml`: persists X/Bluesky/LinkedIn outcome logs.

## Final quality gate

`voice_quality_score()` in `src/growth.py` scores every post before publish:
first person, real stakes, arguable stance, named mechanism, clean opener.
Anything below 7/10 is rejected on LinkedIn, X originals and Bluesky posts.
It also requires a causal connector in the opening lines, so a keyword-stuffed
generic opener cannot score full marks. This is a filter, not a guarantee:
the first 20 published posts still need human review. Visual specs are now
scrubbed of unsourced metrics before render, and "Save this" was removed
from the default attachment.

## Kill criteria (automatic)

- X replies: still 0 successes after the next 10 scheduled attempts → kill the
  workflow step entirely and stop reporting it as a channel.
- X originals: offline failure rate >20% after 20 posts → infra fix before any
  content work.
- Bluesky replies: no `bluesky_replied_uris` growth after 7 days → kill.
- Any unsourced number, off-niche topic or brand remnant reaching a live post →
  immediate hard stop, not a "lesson learned".
- No engagement gain after 20 posts per platform with clean copy → the
  positioning is wrong, not the wording. Change the niche, not the prompts.

I will not buy followers, farm comments, or run engagement pods. Everything
shipped here is real, measurable, and compounding.
