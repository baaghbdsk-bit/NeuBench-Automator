# Swarm Charter — X and Bluesky Engagement

## Mission

Make future X and Bluesky content get materially more engagement. LinkedIn is
already handled; this swarm covers only 𝕏 and Bluesky. The owner has granted full
authority: be aggressive, be blunt, ship.

## Non-negotiable constraints

1. No brand, no product links, no outbound URLs in post bodies.
2. No invented numbers, no fake credentials, no fake telemetry.
3. Audience is AI engineering / LLM benchmarks / developer tools / builder culture.
   No stock prices, no politics, no celebrity gossip, no random cinema roasting.
4. One post per platform per ~6h; existing caps hold (4/day each).
5. No fake followers, no bought engagement, no pods, no deception.
6. Everything must work unattended on GitHub Actions.

## Known baseline (from real data)

- X: 0 successful replies in 39 attempts; 35 skipped for "no suitable target".
  ~46% of original-post attempts failed (Playwright browser missing; fixed in cloud).
  First-person voice exists in X drafts (51/177) but topics drift off-niche (43%).
- Bluesky: 102/130 posts succeeded. Content is technical but often a dense
  one-paragraph explainer with weak hooks; replies never ran until a workflow
  step was added. No outcome measurement on either platform.

## Rules

- Cite evidence: shipped post quote, `file:line`, or sourced external reference.
- Rank by impact × ease. Mark anything that costs more than it returns.
- Write findings to `research/xbsky-<role>.md`. Do not modify production code.
- Return: top 3 findings, single strongest recommendation.
