import argparse
import re
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.linkedin_automater import LinkedInAutomater
from src.linkedin_diagrams import render_transformer_flow_gif
from src.linkedin_state import (
    POST_HISTORY_FILE,
    append_post_entry,
    load_post_history,
    save_post_history,
    utc_now_iso,
)

TITLE = "How a Transformer Reads a Sentence"

POST_TEXT = """A transformer does not read a sentence the way you do.

It turns words into vectors, lets every word look at every other word, then predicts what comes next.

One forward pass, in order:

1. Tokenize.
"The cat sat on the" becomes five tokens. These are the only units the model sees.

2. Embed.
Each token becomes a vector, a list of numbers learned from data. Similar words land near each other.

3. Add position.
Attention has no built-in sense of order. A position signal is added so "cat sat" and "sat cat" are different.

4. Attention.
Every token builds a query, a key, and a value. The query from one token is compared with the keys of all tokens. The scores decide how much of each value to pull in. In a simple subject-verb pattern, "sat" can put more weight on "cat".

5. Feed-forward.
Each position passes through a small network. This refines the representation. It does not mix tokens.

6. Predict.
The final vector is scored against the vocabulary. The top score becomes the next token. The loop repeats with the new token appended.

Stack dozens of these blocks and the same operation turns a prompt into a paragraph.

Which step would you explain first to someone new to LLMs?

#MachineLearning #LLM #DeepLearning #AIEngineering"""

ALT_TEXT = "Animated transformer pipeline: tokens, embeddings, position, attention, feed-forward, and next-token prediction."


def main() -> int:
    parser = argparse.ArgumentParser(description="Render and publish the transformer flow GIF to LinkedIn.")
    parser.add_argument("--dry-run", action="store_true", help="Render and simulate the post without publishing.")
    args = parser.parse_args()

    assets = render_transformer_flow_gif("transformer_flow", frames=60, duration=80)
    gif_path = Path(assets["gif_path"])
    size_mb = gif_path.stat().st_size / (1024 * 1024)
    print(f"GIF: {gif_path}")
    print(f"Size: {size_mb:.2f} MB")
    print(f"Preview: {assets['preview_path']}")
    print(f"Caption: {len(POST_TEXT)} chars")
    print()
    print(POST_TEXT)
    print()

    if size_mb > 8:
        print("Aborting: GIF is too large for LinkedIn.")
        return 1

    automater = LinkedInAutomater(headless=True, dry_run=args.dry_run)
    started = time.time()
    ok, message = automater.post(
        POST_TEXT,
        image_path=str(gif_path),
        media_title=ALT_TEXT,
    )
    print(f"Result: {ok} ({round(time.time() - started, 1)}s)")
    print(message)

    if ok and not args.dry_run:
        urn_match = re.search(r"urn:li:[^\s,)]+", message or "")
        post_urn = urn_match.group(0) if urn_match else ""
        state = load_post_history(POST_HISTORY_FILE)
        append_post_entry(
            state,
            title=TITLE,
            url="",
            content=POST_TEXT,
            status="success",
            posted_at=utc_now_iso(),
            post_urn=post_urn,
        )
        save_post_history(state, POST_HISTORY_FILE)
        print(f"History updated: {POST_HISTORY_FILE}")
        if post_urn:
            print(f"Post URL: https://www.linkedin.com/feed/update/{post_urn}/")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
