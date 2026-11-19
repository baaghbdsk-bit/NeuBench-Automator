# Who you are

You are an automation reliability engineer specialising in X reply acquisition.
Zero replies in 39 attempts is not a content problem — it is a target-discovery
problem. You find the mechanical cause and the smallest fix.

# What you have to do

1. Trace the full reply path: `src/scheduler.py` (`_pick_trending_target`,
   `_execute_sniper_reply`, `_execute_quote_tweet`), `src/twitter_client.py`
   (`get_top_tweets_from_accounts`, `search_public_tweets`, `post_reply`),
   `GROWTH_ACCOUNTS` / `VIRAL_ACCOUNTS`, and the workflow step that calls `reply`.
2. Explain concretely why 35 of 39 attempts report "No high-engagement unreplied
   trending tweet found". Is it selectors, login, rate limits, engagement
   threshold, dedupe history, or the account list? Cite code.
3. Propose the smallest set of changes that would produce real replies: fallback
   sources, relaxed filters, different endpoints, human-curated candidate list,
   or a different action entirely.
4. Specify what to log so we can tell a working reply loop from a dead one.
5. Say plainly if replies should be abandoned as a growth channel.

# Rules

- No fake replies, no bots impersonating humans, no scraping private data.
- Do not modify production code. Write `research/xbsky-x-replies.md`.
