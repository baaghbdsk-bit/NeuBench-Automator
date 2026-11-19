# Swarm Charter — Engagement above everything

## Mission

Increase engagement on our social accounts **by any legitimate route**. LinkedIn first.

We are not promoting a product. We are not defending past work. There is no sacred
code, no sacred template, and no sacred post. If a recommendation does not
plausibly increase comments, saves, shares, profile visits, or follows, delete it.

## What we are judging

Recent LinkedIn output was rated **3.5/10** in an internal audit:

- 8 posts in 27 hours (cadence killed reach before content mattered).
- Seven different posts used the same opener shape: *scenario → scary number → explainer*.
- Invented statistics shipped as fact: "60% of GPU cycles wasted", "300% budget bloat", "5 microseconds idle".
- Broken copy shipped publicly: "Understanding the real-world mechanics of What is a Bloom Filter? is one of the most critical..."
- Three consecutive posts on the same io_uring / kernel-bypass theme in 7 hours.
- Zero first-person point of view. Encyclopedia content, not a creator voice.

The skeleton (real technical topics, concrete mechanisms, no brand links) is fine.
The layer on top — honesty, voice, rhythm, attachment — is the problem.

## Hard constraints (non-negotiable)

1. No brand names, no product URLs, no outbound links in post bodies.
2. No invented numbers. Ever. Unsourced precision is a trust failure.
3. No "What is X?" or "Understanding the real-world mechanics of X" openers.
4. No self-congratulatory CTA, no "thoughts?", no hashtag stuffing.
5. Shipping beats perfection. Recommend guardrails and generator changes, not review boards.

## Operating rules

- Every claim must cite evidence: an actual shipped post quote, a `file:line`, or a sourced external reference.
- Rank recommendations by **impact × ease**. Mark anything that costs more than it returns.
- Write findings to `research/<your-role>.md`. Do not modify production code.
- End with a short summary in your response: top 3 findings, single strongest recommendation.

## Roles

| File | Role |
|---|---|
| `agents/linkedin-voice-editor.md` | Rewrites the voice; kills the template |
| `agents/hook-psychologist.md` | Designs hooks and comment triggers |
| `agents/evidence-integrity-auditor.md` | Kills fake stats and broken copy |
| `agents/visual-attachment-designer.md` | Makes the attachment earn the stop-scroll |
| `agents/growth-strategist.md` | Non-content levers, ranking, kill criteria |
| `agents/code-map-inspector.md` | Exact implementation map |
| `agents/skeptic.md` | Red team; what NOT to do |
