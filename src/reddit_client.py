"""Small Reddit helpers shared by the dashboard and browser publisher."""

from __future__ import annotations

from urllib.parse import quote


class RedditClient:
    TARGET_SUBREDDITS = [
        "r/LocalLLaMA",
        "r/MachineLearning",
        "r/ArtificialInteligence",
        "r/singularity",
        "r/ChatGPT",
    ]

    def get_target_subreddits(self) -> list[str]:
        return list(self.TARGET_SUBREDDITS)

    def generate_submit_url(self, subreddit: str, title: str, body: str) -> str:
        name = subreddit.strip().strip("/")
        if not name.lower().startswith("r/"):
            name = f"r/{name}"
        encoded_title = quote(title or "", safe="")
        encoded_body = quote(body or "", safe="")
        return f"https://www.reddit.com/{name}/submit?title={encoded_title}&text={encoded_body}"
