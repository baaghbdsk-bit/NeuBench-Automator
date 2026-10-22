import os
import urllib.parse
from typing import Dict, Any, List, Optional
import config

TARGET_SUBREDDITS = [
    {
        "name": "r/LocalLLaMA",
        "desc": "Open-source LLMs, quantizations, local hardware benchmarks",
        "flair": "Discussion",
        "url": "https://www.reddit.com/r/LocalLLaMA/"
    },
    {
        "name": "r/MachineLearning",
        "desc": "Academic research, model architecture, ML engineering",
        "flair": "Project / Discussion",
        "url": "https://www.reddit.com/r/MachineLearning/"
    },
    {
        "name": "r/ArtificialInteligence",
        "desc": "Broad industry shifts, frontier AI breakthroughs",
        "flair": "News",
        "url": "https://www.reddit.com/r/ArtificialInteligence/"
    },
    {
        "name": "r/singularity",
        "desc": "Frontier models, AGI roadmaps, capability benchmarks",
        "flair": "AI",
        "url": "https://www.reddit.com/r/singularity/"
    },
    {
        "name": "r/ChatGPT",
        "desc": "Consumer LLMs, real-world productivity & prompt evals",
        "flair": "Discussion",
        "url": "https://www.reddit.com/r/ChatGPT/"
    }
]

class RedditClient:
    """Manages Reddit developer discussions and direct subreddit dispatch."""

    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID", "")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        self.username = os.getenv("REDDIT_USERNAME", "")
        self.password = os.getenv("REDDIT_PASSWORD", "")
        self.user_agent = "NeuBench-Automator/2.0 (by /u/NeuBench)"

    def get_target_subreddits(self) -> List[Dict[str, Any]]:
        return TARGET_SUBREDDITS

    def generate_submit_url(self, subreddit: str, title: str, text: str) -> str:
        """Generates a pre-filled 1-click submit URL for the target subreddit."""
        sub = subreddit.replace("r/", "").strip()
        params = {
            "title": title,
            "text": text
        }
        query = urllib.parse.urlencode(params)
        return f"https://www.reddit.com/r/{sub}/submit?{query}"

    def post(self, subreddit: str, title: str, text: str) -> tuple[bool, str]:
        """Direct PRAW posting if Reddit API credentials are provided in .env."""
        if not (self.client_id and self.client_secret and self.username and self.password):
            submit_url = self.generate_submit_url(subreddit, title, text)
            return True, f"Reddit API credentials not configured in .env. Use 1-Click Submit URL: {submit_url}"

        try:
            import praw
            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=self.username,
                password=self.password,
                user_agent=self.user_agent
            )
            sub = subreddit.replace("r/", "").strip()
            submission = reddit.subreddit(sub).submit(title=title, selftext=text)
            return True, f"https://reddit.com{submission.permalink}"
        except Exception as e:
            return False, f"Reddit submission error: {e}"
