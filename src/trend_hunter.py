import socket
socket.setdefaulttimeout(10)
import feedparser
import requests
import random
import re
from typing import List, Dict, Any, Optional

LINKEDIN_PILLAR_ROTATION = ["NEWS", "EXPLAINER", "DIFFERENCE", "DID_YOU_KNOW", "WHAT_IF", "BEGINNER", "SURVIVAL", "BENCHMARK"]

LINKEDIN_EVERGREEN_TOPICS: Dict[str, List[Dict[str, Any]]] = {
    "EXPLAINER": [
        {
            "title": "How retrieval augmented generation actually works",
            "summary": "A practical explanation of chunking, embedding, retrieval, reranking, and the failure modes teams hit when they ship RAG without measuring retrieval quality.",
            "category": "explainer",
        },
        {
            "title": "What an inference token really costs",
            "summary": "Input tokens, output tokens, cached tokens, and latency all carry different costs. A breakdown of where the bill comes from and which levers actually move it.",
            "category": "explainer",
        },
        {
            "title": "Why KV caching changes long context performance",
            "summary": "A plain explanation of how key value caching avoids recomputing attention, where memory pressure appears, and why long prompts can slow down before they hit a limit.",
            "category": "explainer",
        },
        {
            "title": "What quantization does to model quality",
            "summary": "FP16, INT8, and INT4 reduce memory and cost, but the quality loss is uneven across tasks. A practical guide to when quantization is safe and when it is not.",
            "category": "explainer",
        },
        {
            "title": "How rate limiting protects an API",
            "summary": "Token buckets, concurrency caps, and retry budgets explained for teams that build on top of third party AI APIs.",
            "category": "explainer",
        },
        {
            "title": "What a vector index actually stores",
            "summary": "Embeddings, distance metrics, HNSW graphs, and the tradeoffs between recall, memory, and query latency.",
            "category": "explainer",
        },
    ],
    "DIFFERENCE": [
        {
            "title": "RAG vs fine-tuning: which one to use",
            "summary": "Retrieval augmented generation keeps knowledge outside the model and fetches it at request time. Fine-tuning changes model weights. A practical comparison of cost, freshness, control, and failure modes.",
            "category": "explainer",
        },
        {
            "title": "Latency vs throughput in LLM serving",
            "summary": "Latency is how long one request takes. Throughput is how many requests a system handles per second. The two often trade off, and optimizing one can hurt the other.",
            "category": "explainer",
        },
        {
            "title": "Parameters vs tokens",
            "summary": "Parameters are learned weights inside the model. Tokens are chunks of text processed during inference. A model can have billions of parameters and still bill by tokens.",
            "category": "explainer",
        },
        {
            "title": "Prompt caching vs fine-tuning",
            "summary": "Prompt caching reuses repeated context to lower cost and latency. Fine-tuning changes behavior. They solve different problems and are often combined.",
            "category": "explainer",
        },
    ],
    "DID_YOU_KNOW": [
        {
            "title": "Did you know: attention is not memory",
            "summary": "Attention lets a model weigh other tokens while producing one token. It does not store facts permanently; weights and context do different jobs.",
            "category": "fact",
        },
        {
            "title": "Did you know: temperature changes sampling, not knowledge",
            "summary": "Temperature scales logits before sampling. It makes outputs more or less random, but it does not add facts or improve reasoning by itself.",
            "category": "fact",
        },
        {
            "title": "Did you know: a token is not a word",
            "summary": "Tokenizers split text into subword pieces. Common words may be one token, while rare words become several. This affects cost, context limits, and multilingual performance.",
            "category": "fact",
        },
        {
            "title": "Did you know: quantization can change model behavior",
            "summary": "Lower precision reduces memory and cost, but it can alter outputs unevenly across tasks. Quality should be measured on your own eval set.",
            "category": "fact",
        },
    ],
    "WHAT_IF": [
        {
            "title": "What if your RAG retriever is wrong",
            "summary": "If retrieval returns the wrong chunks, the model can still produce a fluent answer. The fix is to measure recall and precision before blaming generation.",
            "category": "scenario",
        },
        {
            "title": "What if latency matters more than accuracy",
            "summary": "Some products need fast answers more than perfect answers. Routing, caching, and smaller models can matter more than leaderboard rank.",
            "category": "scenario",
        },
        {
            "title": "What if your eval set is too easy",
            "summary": "A benchmark that never fails makes every model look good. Hard cases, edge cases, and real user traces reveal where systems break.",
            "category": "scenario",
        },
        {
            "title": "What if context windows keep growing",
            "summary": "Longer context helps, but cost, latency, and retrieval quality still matter. More tokens are not always better tokens.",
            "category": "scenario",
        },
    ],
    "EXPLAINER": [
        {
            "title": "What an API actually is",
            "summary": "An API is a contract for how software components talk to each other. It defines inputs, outputs, errors, and rules, not just a URL.",
            "category": "explainer",
        },
        {
            "title": "What a framework actually does",
            "summary": "A framework gives structure and conventions, while a library gives reusable functions. The difference is who controls the flow of the program.",
            "category": "explainer",
        },
        {
            "title": "What a database index does",
            "summary": "An index helps a database find rows faster by organizing lookup data. It speeds reads but costs storage and write overhead.",
            "category": "explainer",
        },
        {
            "title": "What JSON is and is not",
            "summary": "JSON is a text format for structured data. It is not a database, schema, or programming language, and it has no comments.",
            "category": "explainer",
        },
        {
            "title": "What an environment variable is",
            "summary": "An environment variable is configuration passed to a process from outside the code. It is useful for secrets and deployment settings, but it is not automatically secure.",
            "category": "explainer",
        },
        {
            "title": "What a webhook is",
            "summary": "A webhook is an HTTP callback triggered by an event. It lets one system notify another instead of polling repeatedly.",
            "category": "explainer",
        },
        {
            "title": "What Docker does",
            "summary": "Docker packages an application with its dependencies into a container. It makes environments more repeatable, but it does not make code correct.",
            "category": "explainer",
        },
        {
            "title": "What Git tracks",
            "summary": "Git tracks snapshots of files, not folders or empty directories. Understanding commits, branches, and remotes prevents common workflow mistakes.",
            "category": "explainer",
        },
    ],
    "DIFFERENCE": [
        {
            "title": "API vs SDK",
            "summary": "An API is the interface. An SDK is a toolkit that helps you use that interface. One defines the contract; the other speeds up implementation.",
            "category": "explainer",
        },
        {
            "title": "Library vs framework",
            "summary": "A library is called by your code. A framework calls your code. That inversion of control is the practical difference.",
            "category": "explainer",
        },
        {
            "title": "Training vs inference",
            "summary": "Training changes model weights using data. Inference uses trained weights to produce outputs. They have different costs, hardware needs, and failure modes.",
            "category": "explainer",
        },
        {
            "title": "Model vs algorithm",
            "summary": "An algorithm is the procedure. A model is the learned result of running that procedure on data. The same algorithm can produce different models.",
            "category": "explainer",
        },
        {
            "title": "Prompt vs context window",
            "summary": "A prompt is what you send. The context window is how much the model can consider at once. A long prompt can crowd out useful context.",
            "category": "explainer",
        },
        {
            "title": "CPU vs GPU for AI",
            "summary": "CPUs handle general sequential work well. GPUs handle many parallel matrix operations well. AI inference often benefits from GPU parallelism, but cost and latency still matter.",
            "category": "explainer",
        },
        {
            "title": "Batch processing vs streaming",
            "summary": "Batching waits for a full set of work and processes it together. Streaming handles items as they arrive. The choice changes latency, throughput, and complexity.",
            "category": "explainer",
        },
        {
            "title": "Cache vs memory",
            "summary": "Memory holds active data for a process. A cache keeps frequently used data closer for faster access. All caches use memory, but not all memory is a cache.",
            "category": "explainer",
        },
        {
            "title": "Git commit vs push",
            "summary": "A commit saves a snapshot locally. A push sends commits to a remote repository. You can commit many times before pushing once.",
            "category": "explainer",
        },
        {
            "title": "JSON vs schema",
            "summary": "JSON is data. A schema is the rulebook that says what that data should look like. Valid JSON can still violate a schema.",
            "category": "explainer",
        },
    ],
    "DID_YOU_KNOW": [
        {
            "title": "Did you know: an API is just a contract",
            "summary": "Behind an API can be a database, a queue, or another service. The API hides implementation details and exposes only agreed inputs and outputs.",
            "category": "fact",
        },
        {
            "title": "Did you know: frameworks are libraries with opinions",
            "summary": "Frameworks reduce decisions by enforcing structure. That can speed development, but it can also make unusual use cases harder.",
            "category": "fact",
        },
        {
            "title": "Did you know: Git does not track empty folders",
            "summary": "Git tracks files, not directories. An empty folder disappears unless it contains a file such as .gitkeep.",
            "category": "fact",
        },
        {
            "title": "Did you know: environment variables are not secrets by default",
            "summary": "Environment variables are convenient, but they can leak through logs, process listings, or child processes. Secret managers add stronger controls.",
            "category": "fact",
        },
        {
            "title": "Did you know: JSON has no comments",
            "summary": "Standard JSON does not allow comments. Some tools accept JSON5 or JSONC, but strict parsers will reject them.",
            "category": "fact",
        },
    ],
    "WHAT_IF": [
        {
            "title": "What if your API has no rate limit",
            "summary": "Without limits, one client can exhaust shared resources and make the service slow for everyone. Rate limits protect availability, not just billing.",
            "category": "scenario",
        },
        {
            "title": "What if you cache the wrong data",
            "summary": "Caching stale or user-specific data can create subtle bugs. Cache keys and invalidation rules matter as much as cache speed.",
            "category": "scenario",
        },
        {
            "title": "What if your prompt is too vague",
            "summary": "Vague prompts force the model to guess intent. Clear constraints, examples, and output formats usually improve results more than longer prompts.",
            "category": "scenario",
        },
        {
            "title": "What if your database has no index",
            "summary": "Queries may still work, but they can scan entire tables. Performance often degrades quietly until traffic grows.",
            "category": "scenario",
        },
    ],
    "BEGINNER": [
        {
            "title": "What is an API in simple terms",
            "summary": "An API is a way for two programs to talk to each other. A clear beginner explanation with a restaurant analogy and one real example.",
            "category": "beginner",
        },
        {
            "title": "What Git actually does",
            "summary": "Git saves snapshots of your code so you can undo mistakes and collaborate. A simple explanation of commits, branches, and remotes.",
            "category": "beginner",
        },
        {
            "title": "What SQL is used for",
            "summary": "SQL is how you ask questions of a database. A beginner-friendly explanation of tables, rows, columns, and simple queries.",
            "category": "beginner",
        },
        {
            "title": "What a variable is",
            "summary": "A variable is a named box that stores a value. A simple explanation for people starting to code.",
            "category": "beginner",
        },
        {
            "title": "What debugging actually means",
            "summary": "Debugging is finding why code does not behave as expected. A beginner guide to reading errors and testing one change at a time.",
            "category": "beginner",
        },
        {
            "title": "How to build your first portfolio",
            "summary": "A first portfolio needs a few small projects, clear README files, and honest explanations. Quality matters more than quantity.",
            "category": "beginner",
        },
        {
            "title": "How to prepare for your first internship",
            "summary": "A practical guide to applying, preparing projects, and talking about what you built without exaggerating.",
            "category": "beginner",
        },
        {
            "title": "How to answer 'tell me about yourself'",
            "summary": "A simple structure for interviews: background, projects, skills, and what you want next. Keep it short and specific.",
            "category": "beginner",
        },
    ],
    "SURVIVAL": [
        {
            "title": "The skills that survive AI automation in 2026",
            "summary": "A grounded look at which engineering and product skills still compound as models absorb routine work, and how to build evidence of those skills in public.",
            "category": "career",
        },
        {
            "title": "How to evaluate an AI tool before your company buys it",
            "summary": "A short evaluation framework covering accuracy on your own data, latency, cost per task, data handling, and the exit path if the vendor changes terms.",
            "category": "career",
        },
        {
            "title": "The 2026 stack for shipping AI features without a platform team",
            "summary": "A minimal stack for small teams: one model provider, one evaluation set, one logging layer, and one fallback path. No overbuilt infrastructure.",
            "category": "career",
        },
        {
            "title": "What to learn first if your role is moving toward AI",
            "summary": "A practical order of study for engineers moving into AI work: evaluation, data quality, latency and cost, then model internals.",
            "category": "career",
        },
        {
            "title": "How to build a personal benchmark for AI tools",
            "summary": "A repeatable way to test models on your own tasks instead of trusting public leaderboards. Includes a small scoring template and a review cadence.",
            "category": "career",
        },
    ],
}

NEWS_SIGNAL_TERMS = (
    "security", "breach", "hack", "cyber", "crypto", "binance", "exchange",
    "regulation", "lawsuit", "antitrust", "outage", "layoff", "hiring",
    "funding", "startup", "chip", "nvidia", "cloud", "data center", "privacy",
    "open source", "acquisition", "ipo", "revenue", "earnings",
)


class TrendHunter:
    """Discovers viral, debated, and breaking topics across the web 100% free with fast RSS & APIs."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def get_google_trends(self, geo: str = "IN") -> List[Dict[str, Any]]:
        """Pulls top real-time trending spikes from Google Trends RSS (Default: India for explosive reach)."""
        trends = []
        for region in [geo, "US"]:
            try:
                url = f"https://trends.google.com/trending/rss?geo={region}"
                feed = feedparser.parse(url)
                for entry in feed.entries[:6]:
                    approx_traffic = getattr(entry, "ht_approx_traffic", "Trending Spike")
                    trends.append({
                        "title": entry.title,
                        "summary": getattr(entry, "summary", entry.title),
                        "source": f"Google Trends ({region})",
                        "traffic": approx_traffic,
                        "category": "breaking_news"
                    })
            except Exception as e:
                print(f"[TrendHunter] Google Trends ({region}) error: {e}")
        return trends

    def get_tech_news(self) -> List[Dict[str, Any]]:
        """Pulls top tech & AI debate stories from Hacker News."""
        news = []
        try:
            top_ids_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            res = requests.get(top_ids_url, timeout=4)
            if res.status_code == 200:
                top_ids = res.json()[:6]
                for item_id in top_ids:
                    item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
                    item = requests.get(item_url, timeout=3).json()
                    if item and "title" in item:
                        news.append({
                            "title": item.get("title", ""),
                            "summary": item.get("title", ""),
                            "comments_count": item.get("descendants", 0),
                            "score": item.get("score", 0),
                            "url": item.get("url", ""),
                            "source": "HackerNews",
                            "category": "ai_tech"
                        })
        except Exception as e:
            print(f"[TrendHunter] HackerNews error: {e}")
        return news

    def get_breaking_rss(self) -> List[Dict[str, Any]]:
        """Pulls breaking tech and world drama from TechCrunch & BBC."""
        items = []
        feeds = [
            ("https://techcrunch.com/feed/", "TechCrunch", "ai_tech"),
            ("http://feeds.bbci.co.uk/news/rss.xml", "BBC World", "breaking_news")
        ]
        for feed_url, source_name, category in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:4]:
                    items.append({
                        "title": entry.title,
                        "summary": getattr(entry, "summary", entry.title)[:200],
                        "url": getattr(entry, "link", ""),
                        "source": source_name,
                        "traffic": "Breaking",
                        "category": category
                    })
            except Exception as e:
                print(f"[TrendHunter] RSS error on {source_name}: {e}")
        return items

    def get_neubench_stories(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Pulls breaking AI benchmark and frontier model insights directly from NeuBench."""
        curated = [
            {
                "title": "Frontier Reasoning Drift & Cost per 1M Tokens (DeepSeek vs Claude vs Gemini)",
                "summary": "NeuBench telemetry reveals significant latency and cost differences when evaluating long-horizon coding tasks across 260+ models.",
                "company": "NeuBench",
                "source": "NeuBench Live Telemetry",
                "traffic": "High Signal AI",
                "category": "ai_tech",
                "url": "https://app.neubench.workers.dev/"
            },
            {
                "title": "Real-World TTFT & Throughput Benchmarks across Major LLM Hosted Endpoints",
                "summary": "NeuBench speed testing shows real-world token throughput variances up to 40% across hosted provider APIs.",
                "company": "NeuBench",
                "source": "NeuBench Latency Radar",
                "traffic": "High Signal AI",
                "category": "ai_tech",
                "url": "https://app.neubench.workers.dev/"
            },
            {
                "title": "Quantized FP8 vs Dense Weights for Autonomous Coding Agents",
                "summary": "NeuBench evaluations analyze benchmark accuracy drop versus inference acceleration on local and cloud models.",
                "company": "NeuBench",
                "source": "NeuBench Model Index",
                "traffic": "High Signal AI",
                "category": "ai_tech",
                "url": "https://app.neubench.workers.dev/"
            },
            {
                "title": "LLM API Outage Frequency & Degradation Index",
                "summary": "NeuBench monitoring tracks endpoint reliability and error rates across top frontier intelligence providers.",
                "company": "NeuBench",
                "source": "NeuBench Reliability Index",
                "traffic": "High Signal AI",
                "category": "ai_tech",
                "url": "https://app.neubench.workers.dev/"
            }
        ]
        return curated[:limit]

    def get_huggingface_daily_papers(self, limit: int = 4) -> List[Dict[str, Any]]:
        """Pulls breaking research papers from Hugging Face Daily Papers API."""
        papers = []
        try:
            res = requests.get("https://huggingface.co/api/daily_papers", timeout=6)
            if res.status_code == 200:
                data = res.json()
                for item in data[:limit]:
                    p = item.get("paper", item)
                    title = p.get("title", "")
                    summary = p.get("summary", title)
                    if title:
                        papers.append({
                            "title": title,
                            "summary": summary[:300],
                            "source": "Hugging Face Daily Papers",
                            "traffic": "Frontier AI Research",
                            "category": "frontier_paper",
                            "url": f"https://huggingface.co/papers/{p.get('id', '')}"
                        })
        except Exception as e:
            print(f"[TrendHunter] Hugging Face Daily Papers error: {e}")
        return papers

    def get_curated_trending_topics(self) -> List[Dict[str, Any]]:
        """Combines and ranks all trends by engagement potential."""
        all_trends = []
        all_trends.extend(self.get_neubench_stories())
        all_trends.extend(self.get_huggingface_daily_papers())
        all_trends.extend(self.get_tech_news())
        all_trends.extend(self.get_breaking_rss())
        all_trends.extend(self.get_google_trends())
        
        random.shuffle(all_trends)
        return all_trends

    def get_linkedin_topics(self, pillar: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return professional LinkedIn topics, optionally filtered to one content pillar."""
        selected = (pillar or "").upper()

        if selected in LINKEDIN_EVERGREEN_TOPICS:
            items = [
                {
                    **topic,
                    "pillar": selected,
                    "source": f"AI {selected.title()} Desk",
                    "url": "",
                }
                for topic in LINKEDIN_EVERGREEN_TOPICS[selected]
            ]
            random.shuffle(items)
            return items

        if selected == "BENCHMARK":
            sources = (self.get_neubench_stories, self.get_huggingface_daily_papers)
        elif selected == "NEWS":
            sources = (self.get_tech_news, self.get_breaking_rss, self.get_neubench_stories)
        else:
            sources = (
                self.get_neubench_stories,
                self.get_huggingface_daily_papers,
                self.get_tech_news,
                self.get_breaking_rss,
            )

        all_topics = []
        for source in sources:
            try:
                all_topics.extend(source())
            except Exception:
                continue

        ai_terms = (
            "artificial intelligence", "machine learning", "deep learning",
            "large language model", "llm", "generative", "foundation model",
            "inference", "transformer", "neural", "robot", "agent",
            "openai", "anthropic", "gemini", "claude", "deepseek", "qwen",
            "mistral", "hugging face", "computer vision", "embedding", "rag",
            "diffusion", "gpu", "benchmark", "model", "token",
        )
        signal_terms = ai_terms + NEWS_SIGNAL_TERMS if selected == "NEWS" else ai_terms

        filtered = []
        seen = set()
        for topic in all_topics:
            title = (topic.get("title") or "").replace("\ufffd", "'").strip()
            summary = (topic.get("summary") or "").replace("\ufffd", "'")
            if not title or title.lower() in seen:
                continue
            haystack = f"{title} {summary}".lower()
            source_name = str(topic.get("source", "")).lower()
            has_signal = bool(re.search(r"\bai\b", haystack)) or any(term in haystack for term in signal_terms)
            trusted_source = "neubench" in source_name or "hugging face" in source_name
            if not trusted_source and not has_signal:
                continue
            seen.add(title.lower())
            filtered.append(
                {
                    **topic,
                    "title": title,
                    "summary": summary,
                    "pillar": selected or "NEWS",
                }
            )

        random.shuffle(filtered)
        return filtered

    def get_casual_topics(self) -> List[Dict[str, Any]]:
        """Return non-tech, everyday relatable, witty, and humorous topics for X and Threads (Indian & global urban lifestyle)."""
        evergreen_casual = [
            # High-Traction Desi / Indian Urban & Workplace Culture
            {"title": "Bengaluru traffic & Silk Board signals", "context": "Spending 45 minutes moving 200 meters in Bangalore traffic while watching your Swiggy delivery guy overtake you on a bicycle."},
            {"title": "The 90-day notice period trauma", "context": "Indian HR enforcing a 90-day notice period like you are an astronaut on an interplanetary mission to Mars."},
            {"title": "Swiggy/Zomato vs 'Ghar pe daal bani hai'", "context": "Carefully customizing your Swiggy cart for 20 minutes only for mom to announce 'Ghar pe daal roti bani hai'."},
            {"title": "Auto-rickshaw 'Nahi jaayega'", "context": "Auto driver looking at you, hearing your destination, and saying 'Nahi jaayega' with the supreme confidence of a billionaire declining an investment."},
            {"title": "The bag of 300 plastic bags", "context": "Every Indian household having one giant master polythene bag under the sink whose sole purpose is to store 300 other polythene bags."},
            {"title": "Mom's cookie tin betrayal", "context": "Opening a Royal Dansk butter cookies tin expecting cookies, only to find needles, buttons, and mom's sewing kit."},
            {"title": "Tatkal booking adrenaline rush at 10:00 AM", "context": "Forget bungee jumping, the real near-death experience is watching the IRCTC Tatkal timer hit 10:00:00 AM while waiting for the OTP."},
            {"title": "The Paytm sound box emotional relief", "context": "Staring intensely at the shopkeeper's QR sound box waiting for the robotic voice to confirm 'Dus rupaye praapt hue'."},
            {"title": "Wedding relatives asking 'Aage ka kya plan hai?'", "context": "A distant uncle you haven't seen in 9 years cornering you near the gulab jamun counter asking 'Aur beta, aage ka kya socha hai?'"},
            {"title": "Surviving corporate shifts on 5 cutting chais", "context": "Running an entire 9-hour corporate workday on 4 cups of cutting chai, two Parle-G biscuits, and pure spite."},
            {"title": "Free dhaniya and mirchi entitlement", "context": "Spending 800 rupees on vegetables and then refusing to leave until the bhaiya gives you free coriander and green chillies."},
            {"title": "Bangalore landlord demands", "context": "Bangalore landlord demanding 10 months security deposit, your 10th-grade board marksheet, and a LinkedIn recommendation."},
            {"title": "Salary credited vs 18th of the month", "context": "Salary credited message on the 1st: 'I will invest in real estate.' Bank balance on the 18th: 'Is tap water a meal?'"},
            {"title": "Typing 'Per my last email'", "context": "Typing 'Per my previous email' when what you really want to say is 'I already answered this, can you please read?'"},
            {"title": "Family WhatsApp 'Good Morning' GIFs", "context": "Waking up to 18 glittery animated roses with quotes like 'Life is a precious gift' in the family WhatsApp group."},
            
            # High-Engagement Conversation & Debate Bait (Massive for Threads Comments)
            {"title": "Everyday scams we normalized", "context": "What is an everyday expense that is a total and complete scam, but society just normalized it?"},
            {"title": "Unwritten public rules broken casually", "context": "What is one unwritten social rule that people break way too casually in public?"},
            {"title": "Unpopular opinion for family dinners", "context": "What is an unpopular opinion that would get you immediately disowned at a family dinner?"},
            {"title": "The age you realized adulthood is a trap", "context": "Drop the exact age you were when you realized adulthood is just being permanently exhausted and doing laundry."},
            {"title": "Overhyped social media purchases", "context": "What is something you bought that was 100% hyped by social media influencers but turned out to be completely useless?"},
            {"title": "Work habits to look busy", "context": "What is a work habit you pretend to have just so nobody gives you extra work?"},

            # Universal Everyday Quirks & Internal Monologues
            {"title": "Second iced coffee at 4 PM", "context": "Drinking cold brew late in the afternoon and then acting shocked when you can't sleep at 2 AM."},
            {"title": "The fridge inspection ritual", "context": "Opening the fridge 12 times in an evening as if new gourmet snacks spawned by magic."},
            {"title": "Canceling weekend plans", "context": "The instantaneous, unrivaled wave of relief when someone cancels the social plans you agreed to 3 weeks ago."},
            {"title": "Grocery store optimism vs reality", "context": "Buying greens with the pure intention of eating clean, only to watch them liquify in the fridge drawer."},
            {"title": "The Sunday 7 PM existential shift", "context": "When the weekend is technically not over, but emotionally you are already in Monday standup."},
            {"title": "Headphones with no music", "context": "Wearing noise-canceling headphones with nothing playing purely as social armor so nobody speaks to you."},
            {"title": "37 alarms set 2 minutes apart", "context": "The delusion that alarm 6:02 AM will wake you up gently after you ignored 5:58, 6:00, and 6:01."},
            {"title": "The post-order tracking panic", "context": "Checking package delivery status 4 minutes after checkout like the courier is going to teleport to your door."},
            {"title": "Work email exclamation marks", "context": "Typing 'Sounds great! No worries at all!' with maximum enthusiasm while looking like an emotionless statue in front of your screen."},
            {"title": "Late-night life motivation", "context": "Deciding at 11:45 PM on a Tuesday that you are going to wake up at 5 AM, run a marathon, and master French, only to hit snooze at 7:30."},
            {"title": "The unread messages spiral", "context": "Having 50 unread messages because answering just one feels like initiating a live hostage negotiation."},
            {"title": "Shopping cart abandonment therapy", "context": "Adding $600 worth of luxury items to an online cart just to feel something, then closing the tab."},
            {"title": "Camera-off telepathy", "context": "The unspoken brotherhood of turning off your camera in a group call the second you see one other person did it."},
            {"title": "Bedtime comeback formulation", "context": "Coming up with the single most devastating, articulate rebuttal to an argument that ended in 2019 while staring at your ceiling."}
        ]
        
        # Try to mix in some lighthearted Google Trends if non-tech
        try:
            spikes = self.get_google_trends(geo="US")
            for sp in spikes:
                title_lower = sp.get("title", "").lower()
                # Exclude tech/AI/politics
                if not any(k in title_lower for k in ("ai", "tech", "election", "trump", "biden", "war", "stock", "gpu", "llm")):
                    evergreen_casual.append({
                        "title": sp.get("title", ""),
                        "context": f"Current trending cultural topic: {sp.get('title')}"
                    })
        except Exception:
            pass

        random.shuffle(evergreen_casual)
        return evergreen_casual

    def get_dynamic_ai_topic(self, used_topics: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Picks a random foundational or frontier AI topic (terminology, architecture, concept, or news)
        with structured components ready for Carousel slides, Shorts voiceover, and Pinterest infographics.
        """
        ai_concept_bank = [
            {
                "title": "Mixture of Experts (MoE)",
                "category": "ARCHITECTURE",
                "tagline": "How Models Get Smarter Without Getting Slower",
                "summary": "Why activate all 70 billion parameters when you only need 14 billion per token? Mixture of Experts uses dynamic routing to activate specialized sub-networks on demand.",
                "problem": "Traditional dense LLMs run all weights on every single word, creating massive compute bottlenecks and sluggish latency.",
                "solution": "MoE introduces a lightweight router network that dynamically sends each token to the top-2 best expert sub-networks.",
                "key_takeaways": [
                    "Sparse activation delivers 70B parameter quality at 14B active compute cost.",
                    "The gating network routes tokens based on semantic context.",
                    "High VRAM footprint is required to keep all expert weights in memory."
                ],
                "pro_tip": "In MoE systems, inference memory bandwidth is the primary bottleneck. Quantizing inactive expert weights to FP8 unlocks massive throughput.",
                "narration": "Think of a dense AI model like a single doctor trying to solve every medical case alone. Mixture of Experts changes everything: a smart router acts like a triage desk, instantly dispatching each token to specialized expert networks. You get the intelligence of a massive model with the speed and cost of a much smaller one!"
            },
            {
                "title": "FlashAttention Explained",
                "category": "INFERENCE & HARDWARE",
                "tagline": "Why Memory Bandwidth Was the Real AI Bottleneck",
                "summary": "Attention in Transformers is quadratic: doubling the prompt quadruples memory traffic. FlashAttention reorganizes GPU memory access to make attention 3x faster without losing accuracy.",
                "problem": "GPUs are fast at math (FLOPs) but slow at moving data between high-bandwidth memory (HBM) and tiny on-chip SRAM cache.",
                "solution": "FlashAttention splits large Q, K, V matrices into small tiles, computing softmax incrementally directly inside fast SRAM cache without writing back to slow HBM.",
                "key_takeaways": [
                    "Transforms memory IO from quadratic O(N^2) to linear O(N).",
                    "Mathematically identical output with zero approximation loss.",
                    "Enabled 32k to 1M+ context windows on standard GPU hardware."
                ],
                "pro_tip": "Always verify FlashAttention-2 or vLLM PagedAttention is enabled in your serving runtime before upgrading GPU hardware.",
                "narration": "Why did long AI prompts used to crash your GPU? Because of memory traffic! GPUs do math instantly, but moving data back and forth to memory takes forever. FlashAttention fixes this by breaking calculations into bite-sized tiles that fit entirely inside high-speed on-chip cache. Result? 3x faster inference and massive context windows!"
            },
            {
                "title": "Quantization: FP16 vs INT8 vs INT4",
                "category": "OPTIMIZATION",
                "tagline": "Running 70B Models on Consumer Hardware",
                "summary": "Quantization shrinks the numerical precision of neural network weights from 16-bit floating point down to 8-bit or 4-bit integers, reducing memory by up to 75% with minimal accuracy loss.",
                "problem": "Running uncompressed 70B models requires 140GB+ of VRAM, pricing out indie builders and local hardware.",
                "solution": "Quantization maps wide 16-bit float ranges into discrete integer buckets using smart scaling factors and outlier preservation.",
                "key_takeaways": [
                    "FP16: 2 bytes per weight (Full precision baseline).",
                    "INT8 (BitsAndBytes): 50% memory cut with virtually zero perplexity drop.",
                    "INT4 (AWQ/GPTQ): 75% memory cut, fitting a 70B model into two 24GB GPUs."
                ],
                "pro_tip": "AWQ (Activation-aware Weight Quantization) protects the 1% most important salient weights, preserving reasoning benchmark scores far better than naive rounding.",
                "narration": "How do you run a giant 70 billion parameter model on a single GPU? Quantization! Instead of storing every weight as a heavy 16-bit number, we compress them into tiny 4-bit integers. It's like converting an uncompressed WAV audio file into a crystal-clear MP3. You cut memory by 75% while keeping the intelligence intact!"
            },
            {
                "title": "LoRA (Low-Rank Adaptation)",
                "category": "TRAINING & ADAPTATION",
                "tagline": "Fine-Tuning Huge Models Without Billions of Weights",
                "summary": "Instead of updating all billions of model parameters during fine-tuning, LoRA freezes the original weights and injects two tiny low-rank matrix adapters, slashing trainable parameters by 99%.",
                "problem": "Full fine-tuning of a 70B model requires updating and storing gigabytes of optimizer states, requiring a multi-node GPU cluster.",
                "solution": "LoRA decomposes the weight update matrix delta-W into two smaller matrices A and B (rank 8 to 64), updating only a fraction of a percent of parameters.",
                "key_takeaways": [
                    "Reduces fine-tuning VRAM requirements by over 70%.",
                    "Allows swapping multiple specialized LoRA adapters on top of one base model at runtime.",
                    "Zero inference latency overhead when merged directly into base weights."
                ],
                "pro_tip": "QLoRA combines 4-bit quantized base models with 16-bit LoRA adapters, allowing you to fine-tune a 70B model on a single desktop RTX 3090/4090 GPU.",
                "narration": "Fine-tuning a modern AI model used to cost thousands of dollars in cloud GPUs. Enter LoRA: Low-Rank Adaptation. Instead of retraining all 70 billion weights, LoRA freezes the entire base model and only trains a tiny pair of adapter matrices. You get 99% of full fine-tuning performance on a single consumer graphics card!"
            },
            {
                "title": "Retrieval-Augmented Generation (RAG)",
                "category": "ARCHITECTURE",
                "tagline": "Giving LLMs an Infinite, Up-to-Date External Brain",
                "summary": "RAG connects language models to live enterprise knowledge bases by converting documents into vector embeddings and dynamically injecting the most relevant snippets into the prompt.",
                "problem": "LLMs suffer from knowledge cutoffs, hallucinate confident falsehoods, and have no visibility into private internal databases.",
                "solution": "RAG converts company docs into vector embeddings. When a question is asked, it retrieves matching context and feeds it directly into the LLM prompt.",
                "key_takeaways": [
                    "Eliminates hallucinations by grounding answers in verified source documents.",
                    "Update enterprise knowledge instantly without expensive model retraining.",
                    "Provides auditable citations and source links for compliance."
                ],
                "pro_tip": "Naive vector search often misses exact keywords. Production systems use Hybrid Search combining BM25 keyword matching with Dense Vector embeddings plus a Cross-Encoder Reranker.",
                "narration": "Why train a new model every time your company updates a document? That's what RAG solves: Retrieval-Augmented Generation. When a user asks a question, your system searches your private docs, grabs the exact relevant paragraphs, and hands them to the AI as an open-book exam. Zero hallucinations, verified citations, instant updates!"
            },
            {
                "title": "KV Cache Optimization",
                "category": "INFERENCE",
                "tagline": "Why Chatbots Slow Down During Long Conversations",
                "summary": "During autoregressive text generation, the Key-Value (KV) cache stores past token attention states so they don't have to be recomputed for every new token. Managing this cache is the key to low-latency AI.",
                "problem": "Without KV caching, generating token 1000 requires recomputing attention for tokens 1 through 999, creating an O(N^2) compute explosion.",
                "solution": "The KV cache stores precomputed Key and Value vectors in GPU memory, turning generation into a blazing fast O(1) step per new token.",
                "key_takeaways": [
                    "Saves enormous compute at the cost of high GPU VRAM consumption.",
                    "Multi-Query Attention (MQA) and Grouped-Query Attention (GQA) reduce KV cache size by 8x.",
                    "PagedAttention eliminates memory fragmentation by managing KV memory like OS virtual memory."
                ],
                "pro_tip": "If your AI endpoint runs out of memory under high concurrency, switch to a model utilizing GQA (Grouped-Query Attention) like Llama 3 or Mistral.",
                "narration": "Ever wonder why an AI response starts fast but starts eating all your GPU memory? It's the KV Cache! To predict the next word, the model needs to remember every previous word's attention keys. By storing them in high-speed memory, it avoids recalculating the whole conversation. Modern architectures like Grouped-Query Attention make this cache 8 times smaller!"
            },
            {
                "title": "Speculative Decoding",
                "category": "ACCELERATION",
                "tagline": "How Draft Models Make Giant LLMs 3x Faster",
                "summary": "Speculative decoding uses a tiny, lightning-fast 'draft model' to guess the next 4-6 tokens, then lets the large frontier model verify them all in a single forward pass.",
                "problem": "Frontier LLMs generate tokens strictly one-by-one. Each token requires moving 100GB+ of weights across memory, leaving GPU compute cores underutilized.",
                "solution": "A small 1B draft model quickly predicts a candidate phrase. The 70B model checks the draft in one parallel batch, accepting correct tokens and correcting mistakes.",
                "key_takeaways": [
                    "Achieves 2x to 3x higher token generation speed without any loss of mathematical accuracy.",
                    "Capitalizes on GPU parallelism: checking 5 tokens takes almost the same time as generating 1.",
                    "Zero retraining required: works out of the box with matching tokenizer pairs."
                ],
                "pro_tip": "Speculative decoding delivers maximum speedups on high-predictability text like code syntax, JSON formats, and structured summaries.",
                "narration": "What if a small AI could write the draft, and a super-smart AI just proofread it? That's Speculative Decoding! A tiny 1-billion model quickly guesses the next 5 words. The huge 70-billion model reviews all 5 in a single glance. If they're right, they get accepted instantly, making generation up to 3 times faster!"
            },
            {
                "title": "Vector Embeddings & Cosine Similarity",
                "category": "FOUNDATIONS",
                "tagline": "How Machines Translate Human Meaning into Geometry",
                "summary": "Vector embeddings convert raw words, code, and images into dense numerical coordinates in high-dimensional space where concepts with similar semantic meaning sit close together.",
                "problem": "Computers understand numbers, not the nuanced meaning of human language or synonyms.",
                "solution": "Embedding models map text into high-dimensional vectors (e.g. 1536 dimensions). Mathematical cosine similarity measures the exact semantic closeness between concepts.",
                "key_takeaways": [
                    "Enables semantic search: 'automobile problems' naturally finds 'car repairs'.",
                    "Captures conceptual relationships: Vector('King') - Vector('Man') + Vector('Woman') ≈ Vector('Queen').",
                    "Forms the mathematical backbone of RAG, recommendation algorithms, and clustering."
                ],
                "pro_tip": "When choosing an embedding model, check the MTEB (Massive Text Embedding Benchmark) leaderboard for top retrieval scores before settling on default models.",
                "narration": "How does an AI know that 'puppy' and 'dog' mean almost the same thing? Vector Embeddings! An embedding model places every concept onto a multidimensional map. Words with similar meanings cluster together. By calculating the angle between vectors, the AI can instantly search millions of documents by concept rather than exact keywords!"
            }
        ]
        
        # Check if we can also use fresh news from TrendHunter
        try:
            stories = self.get_neubench_stories(limit=3)
            papers = self.get_huggingface_daily_papers(limit=3)
            for item in stories + papers:
                title = item.get("title", "")
                summary = item.get("summary", "")
                if title and len(title) > 10:
                    ai_concept_bank.append({
                        "title": title[:70],
                        "category": "FRONTIER AI",
                        "tagline": "Breaking AI Benchmark & Research",
                        "summary": summary[:250],
                        "problem": "Traditional models struggle with real-world latency, cost, and long-horizon reasoning efficiency.",
                        "solution": summary[:180],
                        "key_takeaways": [
                            summary[:100],
                            "Benchmarked continuously on NeuBench live intelligence leaderboards.",
                            "Directly impacts production latency and token economics."
                        ],
                        "pro_tip": "Track live benchmark scores and token speed across 260+ models on app.neubench.workers.dev.",
                        "narration": f"Here is the latest breakthrough in artificial intelligence: {title}. {summary[:150]}. Evaluated live across top models on NeuBench!"
                    })
        except Exception:
            pass

        if used_topics:
            used_set = set(t.lower().strip() for t in used_topics)
            unseen = [item for item in ai_concept_bank if item.get("title", "").lower().strip() not in used_set]
            if unseen:
                return random.choice(unseen)

        return random.choice(ai_concept_bank)

