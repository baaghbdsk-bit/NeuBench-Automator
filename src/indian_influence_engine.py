import os
import json
import time
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from rich.console import Console

console = Console()

_BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = _BASE_DIR / "data"
INDIAN_ACCOUNTS_FILE = DATA_DIR / "indian_accounts.json"
ENGAGEMENT_QUEUE_FILE = DATA_DIR / "engagement_queue.json"

# ==============================================================================
# COMPREHENSIVE SEED DIRECTORY OF INFLUENTIAL INDIAN X ACCOUNTS
# ==============================================================================
INITIAL_INDIAN_ACCOUNTS_SEED: List[Dict[str, Any]] = [
    # --------------------------------------------------------------------------
    # CATEGORY A: POLITICS & GOVERNANCE
    # --------------------------------------------------------------------------
    {
        "username": "narendramodi",
        "name": "Narendra Modi",
        "category": "Politics & Governance",
        "subcategory": "National Leadership",
        "relevance_score": 10,
        "topics": ["National Policy", "Governance", "Global Relations", "Economic Initiatives", "India Development"],
        "is_sensitive": True,
        "priority_tier": 1
    },
    {
        "username": "DrSJaishankar",
        "name": "Dr. S. Jaishankar",
        "category": "Politics & Governance",
        "subcategory": "Diplomacy & Foreign Affairs",
        "relevance_score": 10,
        "topics": ["Geopolitics", "Foreign Policy", "Bharat Stance", "Global Trade"],
        "is_sensitive": True,
        "priority_tier": 1
    },
    {
        "username": "AshwiniVaishnaw",
        "name": "Ashwini Vaishnaw",
        "category": "Politics & Governance",
        "subcategory": "Technology, IT & Railways",
        "relevance_score": 10,
        "topics": ["Semiconductor Mission", "Digital Public Infra", "Railways", "AI Governance"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "ShashiTharoor",
        "name": "Dr. Shashi Tharoor",
        "category": "Politics & Governance",
        "subcategory": "Parliamentarian & Public Intellectual",
        "relevance_score": 9,
        "topics": ["Parliamentary Debates", "Literature", "International Relations", "Education Policy"],
        "is_sensitive": True,
        "priority_tier": 1
    },
    {
        "username": "RahulGandhi",
        "name": "Rahul Gandhi",
        "category": "Politics & Governance",
        "subcategory": "Opposition Leadership",
        "relevance_score": 10,
        "topics": ["Public Policy", "Unemployment", "Social Justice", "Constitution"],
        "is_sensitive": True,
        "priority_tier": 1
    },
    {
        "username": "myogiadityanath",
        "name": "Yogi Adityanath",
        "category": "Politics & Governance",
        "subcategory": "State Leadership",
        "relevance_score": 9,
        "topics": ["UP Development", "Infrastructure", "Law & Order", "State Economy"],
        "is_sensitive": True,
        "priority_tier": 1
    },
    {
        "username": "nitin_gadkari",
        "name": "Nitin Gadkari",
        "category": "Politics & Governance",
        "subcategory": "Infrastructure & Transport",
        "relevance_score": 9,
        "topics": ["Highways", "Expressways", "Green Hydrogen", "Logistics Efficiency"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "AmitShah",
        "name": "Amit Shah",
        "category": "Politics & Governance",
        "subcategory": "Home Affairs & Internal Security",
        "relevance_score": 9,
        "topics": ["Internal Security", "Cooperative Sector", "Border Security", "Legal Reforms"],
        "is_sensitive": True,
        "priority_tier": 1
    },

    # --------------------------------------------------------------------------
    # CATEGORY B: NEWS & JOURNALISM
    # --------------------------------------------------------------------------
    {
        "username": "ANI",
        "name": "Asian News International",
        "category": "News & Journalism",
        "subcategory": "National Wire Service",
        "relevance_score": 10,
        "topics": ["Breaking News", "Press Conferences", "National Developments", "Policy Announcements"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "NDTV",
        "name": "NDTV",
        "category": "News & Journalism",
        "subcategory": "Broadcasting Network",
        "relevance_score": 9,
        "topics": ["Current Affairs", "Business News", "Elections", "Social Issues"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "IndianExpress",
        "name": "The Indian Express",
        "category": "News & Journalism",
        "subcategory": "Investigative & National Print",
        "relevance_score": 9,
        "topics": ["Investigative Journalism", "Explained Series", "Editorial Commentaries", "Judiciary"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "ShekharGupta",
        "name": "Shekhar Gupta",
        "category": "News & Journalism",
        "subcategory": "Political Analyst & Editor",
        "relevance_score": 8,
        "topics": ["CutTheClutter", "National Interest", "Defence Strategy", "Electoral Analysis"],
        "is_sensitive": True,
        "priority_tier": 2
    },
    {
        "username": "ARanganathan72",
        "name": "Anand Ranganathan",
        "category": "News & Journalism",
        "subcategory": "Commentator & Author",
        "relevance_score": 9,
        "topics": ["Policy Debates", "Free Speech", "Scientific Rationalism", "Institutional Accountability"],
        "is_sensitive": True,
        "priority_tier": 1
    },
    {
        "username": "ShivAroor",
        "name": "Shiv Aroor",
        "category": "News & Journalism",
        "subcategory": "Defence & Security Editor",
        "relevance_score": 8,
        "topics": ["Military Modernization", "Air Force", "Geostrategy", "Security Operations"],
        "is_sensitive": False,
        "priority_tier": 2
    },

    # --------------------------------------------------------------------------
    # CATEGORY C: SOCIETY & CULTURE
    # --------------------------------------------------------------------------
    {
        "username": "vikramsampath",
        "name": "Dr. Vikram Sampath",
        "category": "Society & Culture",
        "subcategory": "Historian & Fellow",
        "relevance_score": 8,
        "topics": ["Indian History", "Archival Research", "Cultural Renaissance", "Civilizational Discourse"],
        "is_sensitive": True,
        "priority_tier": 2
    },
    {
        "username": "sanjeevsanyal",
        "name": "Sanjeev Sanyal",
        "category": "Society & Culture",
        "subcategory": "Urban History & Economics",
        "relevance_score": 9,
        "topics": ["Economic History", "Maritime Heritage", "Urban Planning", "Public Administration"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "peakbengaluru",
        "name": "Peak Bengaluru",
        "category": "Society & Culture",
        "subcategory": "Urban Tech & Everyday Culture",
        "relevance_score": 9,
        "topics": ["Startup Life", "Bangalore Traffic", "Tech Quirks", "Urban Relatability"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "anandmahindra",
        "name": "Anand Mahindra",
        "category": "Society & Culture",
        "subcategory": "Business Leader & Cultural Observer",
        "relevance_score": 10,
        "topics": ["Jugaad Innovation", "Indian Talent", "Human Spirit", "Automotive Vision"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "harshgoenka",
        "name": "Harsh Goenka",
        "category": "Society & Culture",
        "subcategory": "Corporate & Social Humor",
        "relevance_score": 8,
        "topics": ["Life Lessons", "Workplace Humor", "Inspiration", "Indian Ingenuity"],
        "is_sensitive": False,
        "priority_tier": 2
    },

    # --------------------------------------------------------------------------
    # CATEGORY D: BUSINESS & TECHNOLOGY
    # --------------------------------------------------------------------------
    {
        "username": "kunalb11",
        "name": "Kunal Shah",
        "category": "Business & Technology",
        "subcategory": "Fintech & Consumer Behavior",
        "relevance_score": 10,
        "topics": ["Delta 4 Framework", "Indian Consumer Psychology", "Wealth Creation", "Startup Truths"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "NandanNilekani",
        "name": "Nandan Nilekani",
        "category": "Business & Technology",
        "subcategory": "Digital Public Infrastructure",
        "relevance_score": 9,
        "topics": ["India Stack", "Aadhaar", "UPI", "AI for Bharat", "Fintech Inclusion"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "Nithin0dha",
        "name": "Nithin Kamath",
        "category": "Business & Technology",
        "subcategory": "Capital Markets & Bootstrapping",
        "relevance_score": 9,
        "topics": ["Stock Markets", "Retail Investing", "Bootstrapping", "Health & Longevity"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "nikhilkamathcio",
        "name": "Nikhil Kamath",
        "category": "Business & Technology",
        "subcategory": "Podcasts & Venture Capital",
        "relevance_score": 8,
        "topics": ["WTF Podcast", "Indian Youth", "Ecosystem Investing", "Macroeconomics"],
        "is_sensitive": False,
        "priority_tier": 2
    },
    {
        "username": "deepigoyal",
        "name": "Deepinder Goyal",
        "category": "Business & Technology",
        "subcategory": "Quick Commerce & Logistics",
        "relevance_score": 9,
        "topics": ["Blinkit", "Zomato", "Quick Commerce Revolution", "Operational Excellence"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "sridharvembhu",
        "name": "Sridhar Vembu",
        "category": "Business & Technology",
        "subcategory": "Deep Tech & Rural Innovation",
        "relevance_score": 9,
        "topics": ["R&D in Bharat", "Rural Industrialization", "Capital Efficiency", "SaaS"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "VarunMayya",
        "name": "Varun Mayya",
        "category": "Business & Technology",
        "subcategory": "AI Creators & Coding",
        "relevance_score": 9,
        "topics": ["AI Agents", "Autonomous Coding", "Future of Work", "Creator Economy"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "IndianTechGuide",
        "name": "Indian Tech Guide",
        "category": "Business & Technology",
        "subcategory": "Tech Ecosystem Radar",
        "relevance_score": 9,
        "topics": ["Tech Breaking News", "Smartphone Market", "EV Tech", "Indian Manufacturing"],
        "is_sensitive": False,
        "priority_tier": 1
    },

    # --------------------------------------------------------------------------
    # CATEGORY E: ENTERTAINMENT & SPORTS
    # --------------------------------------------------------------------------
    {
        "username": "bhogleharsha",
        "name": "Harsha Bhogle",
        "category": "Entertainment & Sports",
        "subcategory": "Cricket Commentary & Storytelling",
        "relevance_score": 9,
        "topics": ["IPL", "Test Cricket", "Indian Cricket Team", "Sportsmanship"],
        "is_sensitive": False,
        "priority_tier": 1
    },
    {
        "username": "cricketaakash",
        "name": "Aakash Chopra",
        "category": "Entertainment & Sports",
        "subcategory": "Cricket Analytics & Broadcast",
        "relevance_score": 8,
        "topics": ["Match Analysis", "T20 Strategy", "Cricket Tactics", "Indian Players"],
        "is_sensitive": False,
        "priority_tier": 2
    },
    {
        "username": "thetanmay",
        "name": "Tanmay Bhat",
        "category": "Entertainment & Sports",
        "subcategory": "Creator Culture & Finance Humor",
        "relevance_score": 9,
            "topics": ["Memes", "Personal Finance", "Internet Culture", "Creator Economy"],
        "is_sensitive": False,
        "priority_tier": 1
    }
]


class IndianInfluenceDatabase:
    """Manages the persistent database of influential Indian public accounts."""

    def __init__(self, db_path: Path = INDIAN_ACCOUNTS_FILE):
        self.db_path = db_path
        self._ensure_storage()

    def _ensure_storage(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            initial_data = {
                "metadata": {
                    "total_accounts": len(INITIAL_INDIAN_ACCOUNTS_SEED),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "focus": "High-Influence Indian X Audience Growth"
                },
                "accounts": {a["username"].lower(): a for a in INITIAL_INDIAN_ACCOUNTS_SEED}
            }
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)

    def load_accounts(self) -> Dict[str, Any]:
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            self._ensure_storage()
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def save_accounts(self, data: Dict[str, Any]):
        data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        data["metadata"]["total_accounts"] = len(data.get("accounts", {}))
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_accounts_by_category(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        data = self.load_accounts()
        accounts = list(data.get("accounts", {}).values())
        if category:
            return [a for a in accounts if a.get("category", "").lower() == category.lower()]
        return accounts

    def get_priority_monitoring_targets(self, tier: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
        accounts = self.get_accounts_by_category()
        # Sort by priority tier ascending (1 is highest), then relevance_score descending
        sorted_accs = sorted(accounts, key=lambda a: (a.get("priority_tier", 2), -a.get("relevance_score", 5)))
        filtered = [a for a in sorted_accs if a.get("priority_tier", 2) <= tier]
        return filtered[:limit]

    def update_account_activity(self, username: str, metrics_delta: Optional[Dict[str, Any]] = None):
        data = self.load_accounts()
        uname = username.lower()
        if uname in data.get("accounts", {}):
            acc = data["accounts"][uname]
            acc["last_monitored"] = datetime.now(timezone.utc).isoformat()
            if metrics_delta:
                acc.setdefault("engagement_history", []).append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **metrics_delta
                })
            self.save_accounts(data)

    def add_or_update_account(self, account_dict: Dict[str, Any]):
        data = self.load_accounts()
        uname = account_dict.get("username", "").lower().strip("@")
        if not uname:
            return
        account_dict["username"] = uname
        account_dict["profile_url"] = f"https://x.com/{uname}"
        data.setdefault("accounts", {})[uname] = account_dict
        self.save_accounts(data)


class OpportunityQueueManager:
    """
    Manages the engagement opportunity queue with sensitivity categorization,
    human approval gating for political/communal issues, and deduplication.
    """

    def __init__(self, queue_path: Path = ENGAGEMENT_QUEUE_FILE):
        self.queue_path = queue_path
        self._ensure_storage()

    def _ensure_storage(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not self.queue_path.exists():
            initial_data = {
                "metadata": {
                    "total_opportunities": 0,
                    "pending_approval": 0,
                    "approved": 0,
                    "published": 0,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                },
                "opportunities": []
            }
            with open(self.queue_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)

    def load_queue(self) -> Dict[str, Any]:
        try:
            with open(self.queue_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            self._ensure_storage()
            with open(self.queue_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def save_queue(self, data: Dict[str, Any]):
        opps = data.get("opportunities", [])
        data["metadata"]["total_opportunities"] = len(opps)
        data["metadata"]["pending_approval"] = sum(1 for o in opps if o.get("status") == "pending_approval")
        data["metadata"]["approved"] = sum(1 for o in opps if o.get("status") == "approved")
        data["metadata"]["published"] = sum(1 for o in opps if o.get("status") == "published")
        data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.queue_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def is_url_enqueued(self, tweet_url: str) -> bool:
        data = self.load_queue()
        return any(o.get("tweet_url") == tweet_url for o in data.get("opportunities", []))

    def enqueue_opportunity(
        self,
        tweet_url: str,
        author: str,
        tweet_text: str,
        category: str,
        suggested_reply: str,
        why_relevant: str,
        is_sensitive: bool = False
    ) -> Dict[str, Any]:
        data = self.load_queue()
        if any(o.get("tweet_url") == tweet_url for o in data.get("opportunities", [])):
            return {}

        status = "pending_approval" if is_sensitive else "approved"
        opportunity = {
            "id": f"opp_{int(time.time())}_{author.lower()}",
            "tweet_url": tweet_url,
            "author": author,
            "category": category,
            "tweet_text": tweet_text,
            "suggested_reply": suggested_reply,
            "why_relevant": why_relevant,
            "is_sensitive": is_sensitive,
            "status": status,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "published_at": None,
            "result_message": ""
        }
        data.setdefault("opportunities", []).append(opportunity)
        self.save_queue(data)
        return opportunity

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        data = self.load_queue()
        return [o for o in data.get("opportunities", []) if o.get("status") == "pending_approval"]

    def get_ready_to_publish(self, limit: int = 1) -> List[Dict[str, Any]]:
        data = self.load_queue()
        return [o for o in data.get("opportunities", []) if o.get("status") == "approved"][:limit]

    def mark_published(self, opportunity_id: str, success: bool, msg: str = ""):
        data = self.load_queue()
        for o in data.get("opportunities", []):
            if o.get("id") == opportunity_id:
                o["status"] = "published" if success else "failed"
                o["published_at"] = datetime.now(timezone.utc).isoformat()
                o["result_message"] = msg
                break
        self.save_queue(data)

    def approve_opportunity(self, opportunity_id: str):
        data = self.load_queue()
        for o in data.get("opportunities", []):
            if o.get("id") == opportunity_id:
                o["status"] = "approved"
                break
        self.save_queue(data)


class IndianEngagementEngine:
    """
    Core engine orchestrating Indian account monitoring, intelligent conversation discovery,
    fact-based and witty response synthesis, and queue management.
    """

    def __init__(self, twitter_client=None, ai_generator=None, tracker=None):
        from src.twitter_client import TwitterClient
        from src.ai_generator import AIGenerator
        from src.tracker import ActivityTracker
        import config

        self.db = IndianInfluenceDatabase()
        self.queue = OpportunityQueueManager()
        self.twitter = twitter_client or TwitterClient(headless=True)
        self.ai = ai_generator or AIGenerator()
        self.tracker = tracker or ActivityTracker(Path("trial_metrics.json"), Path("post_history.json"))

    def detect_sensitivity(self, text: str, category: str) -> Tuple[bool, str]:
        """
        Classifies whether a discussion involves sensitive political, religious, or communal topics
        requiring mandatory human approval.
        """
        text_lower = text.lower()
        
        # High sensitivity triggers: communal conflicts, election litigation, religious friction
        communal_keywords = [
            "hindu-muslim", "communal", "riot", "caste census", "waqf",
            "temple demolition", "mosque", "reservation bill", "sanatan debate",
            "blasphemy", "conversion", "sedition", "supreme court stay"
        ]
        for kw in communal_keywords:
            if kw in text_lower:
                return True, f"Triggered sensitive societal/communal keyword: '{kw}'"

        if category == "Politics & Governance":
            political_friction = ["corrupt", "jail", "arrest", "scam", "rigged", "evm"]
            for pf in political_friction:
                if pf in text_lower:
                    return True, f"Political controversy keyword: '{pf}'"

        return False, "Standard public policy or cultural discussion"

    def synthesize_indian_reply(self, author: str, tweet_text: str, category: str) -> str:
        """
        Synthesizes a high-signal response calibrated for Indian X discourse:
        - Factual grounding
        - Witty, insightful, respectful disagreement or value-add observation
        - Culturally tuned, natural English / Hinglish nuance where appropriate
        """
        prompt = f"""
Influential Indian Public Figure: @{author}
Category: {category}
Original Tweet:
"{tweet_text}"

You are an insightful, sharp, and culturally astute commentator participating in high-visibility Indian X public discourse.
Task:
Craft a brilliant, concise, and thought-provoking reply to @{author}'s tweet.

Guidelines:
1. Tone: Highly intelligent, culturally authentic, respectful but witty.
2. Substance: Add a concrete fact, historical parallel, policy perspective, or sharp observation.
3. If disagreeing: Be constructive, data-grounded, and respectful. Zero abuse, zero partisan trolling.
4. If appreciating: Elevate the point beyond basic flattery.
5. Strict constraints:
   - Under 240 characters.
   - Do NOT include @mention or quotes.
   - 100% human voice. No bot cliches ("Great initiative sir!", "Totally agree!").
Output ONLY the reply text.
"""
        system_prompt = (
            "You are an articulate, knowledgeable Indian public intellectual and tech commentator. "
            "You write concise, factually grounded, and culturally sharp replies that earn high engagement and respect on Indian X."
        )
        return self.ai._generate_with_fallback(prompt, system_prompt, temperature=0.85).strip('"').strip()

    def monitor_and_discover_opportunities(self, sample_size: int = 4) -> List[Dict[str, Any]]:
        """
        Monitors a sample of priority Indian public accounts, discovers active conversations,
        and enqueues high-value engagement opportunities.
        """
        import random
        priority_accounts = self.db.get_priority_monitoring_targets(tier=2, limit=25)
        candidates = random.sample(priority_accounts, min(sample_size, len(priority_accounts)))
        
        discovered_opportunities: List[Dict[str, Any]] = []
        console.print(f"\n[bold cyan]🇮🇳 Monitoring {len(candidates)} Influential Indian X Accounts...[/bold cyan]")

        for acc in candidates:
            username = acc["username"]
            category = acc.get("category", "Society & Culture")
            console.print(f"[dim]Inspecting latest activity from @{username} ({acc['name']})...[/dim]")
            
            tweet_data = self.twitter.get_latest_tweet_from_account(username)
            url = tweet_data.get("tweet_url")
            text = tweet_data.get("tweet_text")

            if not url or not text or len(text) < 20:
                continue

            # Check if already replied in post_history or already in queue
            already_replied = url in self.tracker.history.get("replied_urls", [])
            already_queued = self.queue.is_url_enqueued(url)

            if already_replied or already_queued:
                console.print(f"[dim]Already engaged or queued for {url}.[/dim]")
                continue

            console.print(f"[bold green]🎯 Found active post by @{username}:[/bold green] {text[:75]}...")
            
            # Detect sensitivity
            is_sensitive, reason = self.detect_sensitivity(text, category)
            if acc.get("is_sensitive", False) and category == "Politics & Governance":
                is_sensitive = True

            # Synthesize reply
            try:
                suggested_reply = self.synthesize_indian_reply(username, text, category)
                console.print(f"[yellow]Suggested Reply ({'⚠️ PENDING APPROVAL' if is_sensitive else '✅ APPROVED'}):[/yellow] {suggested_reply}")
            except Exception as e:
                console.print(f"[red]Error synthesizing reply: {e}[/red]")
                continue

            why_relevant = f"High-influence Indian voice in {category}. Active debate on: {text[:60]}"
            opp = self.queue.enqueue_opportunity(
                tweet_url=url,
                author=username,
                tweet_text=text,
                category=category,
                suggested_reply=suggested_reply,
                why_relevant=why_relevant,
                is_sensitive=is_sensitive
            )
            if opp:
                discovered_opportunities.append(opp)
                self.db.update_account_activity(username, {"action": "opportunity_enqueued", "tweet_url": url})

        console.print(f"[bold green]✅ Discovered & enqueued {len(discovered_opportunities)} Indian engagement opportunity(ies)![/bold green]\n")
        return discovered_opportunities

    def process_approved_queue(self, dry_run: bool = False, max_actions: int = 1) -> int:
        """Publishes approved non-sensitive replies from the queue."""
        ready = self.queue.get_ready_to_publish(limit=max_actions)
        if not ready:
            console.print("[dim]No approved opportunities in queue ready to publish.[/dim]")
            return 0

        published_count = 0
        for opp in ready:
            opp_id = opp["id"]
            url = opp["tweet_url"]
            reply_text = opp["suggested_reply"]
            author = opp["author"]

            console.print(f"\n[bold cyan]🚀 Publishing Indian Engagement to @{author}:[/bold cyan]")
            console.print(f"[dim]URL: {url}[/dim]")
            console.print(f"[green]Reply: {reply_text}[/green]")

            if dry_run or getattr(self.twitter, "dry_run", False):
                console.print(f"[TwitterClient] [DRY RUN] Would publish reply to @{author}: {reply_text}")
                self.queue.mark_published(opp_id, success=True, msg="[DRY RUN] Simulated publish")
                published_count += 1
            else:
                ok = self.twitter.post_reply(url, reply_text)
                if ok:
                    self.tracker.record_event(
                        action_type="indian_reply",
                        status="success",
                        target_identifier=url,
                        content_preview=reply_text,
                        is_dry_run=False
                    )
                    self.queue.mark_published(opp_id, success=True, msg="Confirmed published via Playwright")
                    published_count += 1
                else:
                    self.queue.mark_published(opp_id, success=False, msg="Playwright submission failed")

        return published_count

    def generate_audit_summary(self) -> Dict[str, Any]:
        """Provides a comprehensive report on discovered accounts, categories, and queue status."""
        acc_data = self.db.load_accounts()
        q_data = self.queue.load_queue()
        
        accounts = list(acc_data.get("accounts", {}).values())
        categories = {}
        for a in accounts:
            cat = a.get("category", "General")
            categories[cat] = categories.get(cat, 0) + 1

        pending = self.queue.get_pending_approvals()

        return {
            "total_accounts_discovered": len(accounts),
            "categories_breakdown": categories,
            "total_opportunities_queued": len(q_data.get("opportunities", [])),
            "pending_approval_count": len(pending),
            "pending_approvals": pending[:5],
            "approved_ready_count": q_data.get("metadata", {}).get("approved", 0),
            "technical_limitations": [
                "Official X API Free Tier offers 0 search/mention endpoints; module utilizes stealth Playwright session.",
                "Scrapes public conversation trees safely with randomized human keystroke delay (30-80ms).",
                "Strict rate limit: max 1 Indian reply per 2-hour cycle to avoid platform spam flags."
            ]
        }
