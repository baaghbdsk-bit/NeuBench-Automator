# Growth Playbook

The accounts are creator accounts. There is no product being promoted. Every
change in this repository is judged by one question: **does it increase reach,
engagement, or followers?**

## Positioning

- One voice across all three platforms: AI engineering, LLM benchmarks,
  developer tooling, builder culture.
- No brand names, no product URLs, no CTA links in post bodies. Outbound links
  suppress reach on X and LinkedIn.
- Posts open with a concrete claim, number, or trade-off. No "In today's...",
  no "game changer", no generic hashtag stuffing.
- Reply before posting: a good reply under an account your audience already
  follows reaches more people than another original post.

## Cadence

| Platform | Original posts/day | Interval | Why |
|---|---:|---|---|
| 𝕏 | 4 | ~6h | Fast feedback loop; mix of 70% evergreen takes, 30% live signals |
| Bluesky | 4 | ~6h | Technical audience, tolerant of volume, cheap API |
| LinkedIn | **1** | 12h minimum | >1/day suppresses reach on professional feeds |

Engagement targets: 6 LinkedIn peer comments/day, X sniper replies every
6h, Bluesky replies every 6h (each reply target is deduped).

## Guardrails in code

- `src/growth.py` sanitizes every published string: strips brand mentions,
  URLs, and dangling labels; repairs capitalisation afterwards.
- Jaccard topic similarity blocks near-duplicate LinkedIn topics, across both
  live signals and AI-ideated topics.
- X originals are blended toward the evergreen builder-topic bank in
  `TrendHunter.get_x_growth_topics()` so the account stops competing with
  millions of generic trend posts.
- X reply targets are biased toward AI/tech builders, and profiles are scanned
  in a single browser session instead of launching one browser per account.
- LinkedIn is capped at one post/day both in `config.py` and in the workflow
  environment, with a 12-hour cooldown.

## Metrics to watch (next 2 weeks)

1. **X impressions and profile visits** per post — should rise once links and
   roasting topics are gone.
2. **Reply acceptance** — the previous failure mode was "no target found" on
   34 of 38 runs. If this stays high, the scraper needs selector work, not
   more prompts.
3. **LinkedIn saves/comments per post** — with 1 post/day this is the cleanest
   signal of whether the long-form angle works.
4. **Follower deltas** from `data/x_followers.json` (now persisted by the
   cloud workflow).
5. **Repeat topics** — dedupe should eliminate cases like two `io_uring`
   posts hours apart.

## Remaining risks

- Profile artwork files still have brand-based filenames
  (`assets/neubench_avatar.jpg`, banners, etc.). The text in the profile setup
  scripts is neutral, but the images themselves may still contain brand marks
  and should be replaced by the owner of the visual identity.
- LinkedIn engagement runs in its own concurrency group now. If it still
  produces no events after this release, the next place to look is browser
  session authentication (`LINKEDIN_COOKIES_BASE64`), not the schedule.
- One pre-existing test (`test_missing_confirmation_is_unknown_not_success`)
  fails on the upstream commit before these changes too; it is unrelated to
  the growth work.
