import socket
socket.setdefaulttimeout(10)
import feedparser
import requests
import random
import re
import html
import hashlib
import json
import urllib.parse
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple, Union

from src.x_state import atomic_write_json, normalize_x_text, content_hash

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

# ==============================================================================
# DETERMINISTIC TREND RANKING & SENSITIVITY CONFIGURATION
# ==============================================================================

DEFAULT_SOURCE_WEIGHTS: Dict[str, float] = {
    # High-signal verified benchmark telemetry and frontier research
    "NeuBench Live Telemetry": 9.5,
    "Hugging Face Daily Papers": 9.0,
    # High-signal developer and public discussions
    "HackerNews": 8.5,
    "Google Trends (IN)": 8.5,  # India-first primary audience growth target
    "TechCrunch": 8.0,
    "BBC World": 7.5,
    "Google Trends (US)": 7.0,
}
DEFAULT_UNKNOWN_SOURCE_WEIGHT: float = 6.0

DEFAULT_CATEGORY_MULTIPLIERS: Dict[str, float] = {
    "frontier_paper": 1.15,
    "ai_tech": 1.10,
    "breaking_news": 1.0,
    "society_culture": 1.0,
    "explainer": 1.05,
}

COMMUNAL_RELIGIOUS_TRIGGERS: Tuple[str, ...] = (
    "hindu-muslim", "communal", "riot", "caste census", "waqf",
    "temple demolition", "mosque", "reservation bill", "sanatan debate",
    "blasphemy", "conversion", "sedition", "supreme court stay",
    "lynching", "communal violence", "religious clash"
)

POLITICAL_CRIMINAL_FRICTION_TRIGGERS: Tuple[str, ...] = (
    "corrupt", "jail", "arrest", "scam", "rigged", "evm",
    "custody", "defamation", "allegations", "rape", "murder",
    "suicide", "terrorist", "encounter", "extortion", "bribe"
)


def detect_trend_sensitivity(title: str, summary: str = "", category: str = "") -> Tuple[bool, str]:
    """
    Classifies whether a discovered trend touches sensitive political, religious, communal,
    or criminal controversies requiring mandatory human review before publishing.
    """
    text_corpus = f"{title} {summary}".lower()

    for kw in COMMUNAL_RELIGIOUS_TRIGGERS:
        if kw in text_corpus:
            return True, f"Triggered sensitive societal/communal trigger: '{kw}'"

    category_norm = (category or "").lower()
    if category_norm in ("breaking_news", "politics", "society_culture") or "google trends" in category_norm:
        for pf in POLITICAL_CRIMINAL_FRICTION_TRIGGERS:
            pattern = rf"\b{re.escape(pf)}\b"
            if re.search(pattern, text_corpus):
                return True, f"Political/criminal controversy trigger: '{pf}'"

    return False, "Standard public interest or tech topic"


def canonicalize_url(url: Optional[str]) -> str:
    """
    Normalizes a URL by stripping tracking parameters, normalizing scheme/host,
    and stripping trailing slashes.
    """
    if not url or not isinstance(url, str):
        return ""
    clean = url.strip()
    if not clean or not clean.startswith(("http://", "https://")):
        return ""
    try:
        parsed = urllib.parse.urlsplit(clean)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        tracking_prefixes = ("utm_", "fbclid", "gclid", "ref", "mc_cid", "mc_eid")
        filtered_params = [
            (k, v) for k, v in query_params
            if not any(k.lower().startswith(p) for p in tracking_prefixes)
        ]
        new_query = urllib.parse.urlencode(filtered_params)
        path = parsed.path.rstrip("/")
        return urllib.parse.urlunsplit((parsed.scheme.lower(), netloc, path, new_query, ""))
    except Exception:
        return clean.rstrip("/")


def normalize_trend_title(title: str) -> str:
    """
    Normalizes title text for deduplication: unescapes HTML entities, removes common
    publisher trailing suffixes, strips punctuation, and collapses whitespace.
    """
    if not title:
        return ""
    text = html.unescape(title)
    text = re.sub(
        r"\s+[-|–—]\s+(?:BBC News|TechCrunch|Hacker News|The Verge|Reuters|NDTV|The Indian Express).*$",
        "",
        text,
        flags=re.IGNORECASE
    )
    return normalize_x_text(text)


def generate_trend_id(url: str, title: str) -> str:
    """
    Generates a deterministic 16-character identifier based on canonical URL or normalized title.
    """
    canon_url = canonicalize_url(url)
    if canon_url:
        key = f"url:{canon_url}"
    else:
        key = f"title:{normalize_trend_title(title)}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"tr_{digest}"


def normalize_trend_item(
    raw: Dict[str, Any],
    source: str,
    default_category: str = "breaking_news",
    discovered_at: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Converts raw feed/API entries into a strict, consistent Trend representation.
    Handles missing fields gracefully without inventing synthetic values.
    """
    if not isinstance(raw, dict):
        return None

    raw_title = str(raw.get("title") or "").strip()
    if not raw_title or len(raw_title) < 3:
        return None

    title = html.unescape(raw_title).replace("\ufffd", "'").strip()
    raw_summary = str(raw.get("summary") or raw.get("context") or title).strip()
    summary = html.unescape(raw_summary).replace("\ufffd", "'").strip()

    url = canonicalize_url(raw.get("url") or raw.get("link") or "")
    trend_id = generate_trend_id(url, title)

    category = raw.get("category") or default_category

    # Extract published_at if present without fabricating
    published_at: Optional[str] = None
    raw_pub = raw.get("published_at") or raw.get("published")
    if isinstance(raw_pub, str) and raw_pub.strip():
        published_at = raw_pub.strip()
    elif "published_parsed" in raw and raw["published_parsed"]:
        try:
            dt = datetime(*raw["published_parsed"][:6], tzinfo=timezone.utc)
            published_at = dt.isoformat()
        except Exception:
            published_at = None
    elif "time" in raw and isinstance(raw["time"], (int, float)):
        try:
            dt = datetime.fromtimestamp(raw["time"], tz=timezone.utc)
            published_at = dt.isoformat()
        except Exception:
            published_at = None

    disc_at = discovered_at or raw.get("discovered_at") or datetime.now(timezone.utc).isoformat()

    # Sensitivity detection
    is_sensitive, sens_reason = detect_trend_sensitivity(title, summary, category)
    if raw.get("is_sensitive") is True:
        is_sensitive = True
        sens_reason = raw.get("sensitivity_reason", sens_reason)

    # Clean metadata signals (preserving authentic source signals, no fabrication)
    metadata: Dict[str, Any] = {
        "sources_seen": [source],
        "sensitivity_reason": sens_reason,
        "traffic": raw.get("traffic") if raw.get("traffic") != "Trending Spike" else None,
        "hn_score": raw.get("score") if isinstance(raw.get("score"), int) else None,
        "hn_comments": raw.get("comments_count") if isinstance(raw.get("comments_count"), int) else None,
        "company": raw.get("company"),
        "pillar": raw.get("pillar"),
    }
    metadata = {k: v for k, v in metadata.items() if v is not None}

    item = {
        "id": trend_id,
        "title": title,
        "summary": summary,
        "source": source,
        "category": category,
        "url": url,
        "score": 0.0,
        "discovered_at": disc_at,
        "published_at": published_at,
        "is_sensitive": is_sensitive,
        "metadata": metadata,
        # Backwards compatibility aliases
        "context": summary,
        "traffic": raw.get("traffic", "Trending Spike"),
    }
    return item


def calculate_trend_score(
    item: Dict[str, Any],
    weights_config: Optional[Dict[str, Any]] = None
) -> float:
    """
    Calculates a deterministic relevance score for a trend item.
    Formula:
      score = (source_weight * category_multiplier) + engagement_boost + recency_factor + multi_source_boost

    Rules:
    - Never fabricates engagement or velocity metrics if missing.
    - Missing metrics contribute 0.0 to their specific boost term.
    - Recency factor applies only when published_at is verifiable.
    """
    weights = weights_config or {}
    source_weights = weights.get("source_reliability", DEFAULT_SOURCE_WEIGHTS)
    category_weights = weights.get("category_weights", DEFAULT_CATEGORY_MULTIPLIERS)

    source = item.get("source", "")
    base_score = source_weights.get(source)
    if base_score is None:
        for k, v in source_weights.items():
            if k.lower() in source.lower():
                base_score = v
                break
    if base_score is None:
        base_score = DEFAULT_UNKNOWN_SOURCE_WEIGHT

    category = item.get("category", "breaking_news")
    category_multiplier = category_weights.get(category, 1.0)

    # Engagement boost (ONLY from authentic signals in item/metadata)
    meta = item.get("metadata", {})
    engagement_boost = 0.0

    hn_score = meta.get("hn_score")
    if isinstance(hn_score, (int, float)) and hn_score > 0:
        engagement_boost += min(hn_score / 50.0, 3.0)

    hn_comments = meta.get("hn_comments")
    if isinstance(hn_comments, (int, float)) and hn_comments > 0:
        engagement_boost += min(hn_comments / 30.0, 2.0)

    traffic_str = str(meta.get("traffic") or "")
    if "M+" in traffic_str:
        try:
            val = float(traffic_str.replace("M+", "").strip())
            engagement_boost += min(3.5 + val * 0.5, 5.0)
        except Exception:
            engagement_boost += 3.5
    elif "K+" in traffic_str:
        try:
            val = float(traffic_str.replace("K+", "").strip())
            if val >= 500:
                engagement_boost += 3.0
            elif val >= 200:
                engagement_boost += 2.5
            elif val >= 100:
                engagement_boost += 2.0
            elif val >= 50:
                engagement_boost += 1.5
            elif val >= 10:
                engagement_boost += 1.0
        except Exception:
            engagement_boost += 1.0

    # Recency factor (only if published_at is present and valid)
    recency_factor = 0.0
    pub_at_str = item.get("published_at")
    if pub_at_str:
        try:
            pub_dt = datetime.fromisoformat(pub_at_str.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            elapsed_hours = (now_dt - pub_dt).total_seconds() / 3600.0
            if elapsed_hours <= 3.0:
                recency_factor = 2.0
            elif elapsed_hours <= 12.0:
                recency_factor = 1.0
            elif elapsed_hours <= 24.0:
                recency_factor = 0.5
            elif elapsed_hours <= 48.0:
                recency_factor = 0.0
            else:
                recency_factor = -0.5
        except Exception:
            recency_factor = 0.0

    # Multi-source boost
    sources_seen = meta.get("sources_seen", [source])
    multi_source_boost = 0.0
    if len(sources_seen) > 1:
        multi_source_boost = min(2.0 * (len(sources_seen) - 1), 4.0)

    total_score = (base_score * category_multiplier) + engagement_boost + recency_factor + multi_source_boost
    return round(total_score, 2)


def rank_trends(
    items: List[Dict[str, Any]],
    weights_config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Ranks items deterministically by calculated score descending, tie-breaking by
    discovered_at descending, then id ascending.
    """
    for item in items:
        item["score"] = calculate_trend_score(item, weights_config)

    return sorted(
        items,
        key=lambda x: (
            -x.get("score", 0.0),
            x.get("discovered_at", ""),
            x.get("id", "")
        )
    )


def _title_tokens(title: str) -> Set[str]:
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "of", "from"}
    norm = normalize_trend_title(title)
    words = re.findall(r"\b\w{3,}\b", norm)
    return {w for w in words if w not in stopwords}


def deduplicate_trends(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates items across sources by canonical URL, normalized title hash,
    or high token overlap, while preserving source attribution and multi-source signals.
    """
    merged_by_id: Dict[str, Dict[str, Any]] = {}
    url_to_id: Dict[str, str] = {}
    title_hash_to_id: Dict[str, str] = {}

    for item in items:
        if not item or not isinstance(item, dict):
            continue

        item_id = item.get("id")
        url = item.get("url")
        title = item.get("title", "")
        source = item.get("source")

        norm_title = normalize_trend_title(title)
        title_hash = hashlib.sha256(norm_title.encode("utf-8")).hexdigest()
        tokens = _title_tokens(title)

        target_id: Optional[str] = None

        if item_id in merged_by_id:
            target_id = item_id
        elif url and url in url_to_id:
            target_id = url_to_id[url]
        elif title_hash in title_hash_to_id:
            target_id = title_hash_to_id[title_hash]
        else:
            if len(tokens) >= 4:
                for existing_id, existing_item in merged_by_id.items():
                    existing_tokens = _title_tokens(existing_item.get("title", ""))
                    if len(existing_tokens) >= 4:
                        intersection = tokens.intersection(existing_tokens)
                        union = tokens.union(existing_tokens)
                        if union and (len(intersection) / len(union)) >= 0.75:
                            target_id = existing_id
                            break

        if target_id and target_id in merged_by_id:
            target = merged_by_id[target_id]
            seen_sources = target.setdefault("metadata", {}).setdefault("sources_seen", [target.get("source")])
            if source and source not in seen_sources:
                seen_sources.append(source)

            # Prefer richer summary
            if len(item.get("summary", "")) > len(target.get("summary", "")):
                target["summary"] = item["summary"]
                target["context"] = item["summary"]

            # Retain canonical URL if target lacks one
            if not target.get("url") and url:
                target["url"] = url
                url_to_id[url] = target_id

            # Merge metadata signals without overwriting existing authentic signals
            for k in ("traffic", "hn_score", "hn_comments", "company"):
                if item.get("metadata", {}).get(k) and not target.get("metadata", {}).get(k):
                    target["metadata"][k] = item["metadata"][k]

            # Preserve sensitive classification if triggered by either source
            if item.get("is_sensitive"):
                target["is_sensitive"] = True
                target["metadata"]["sensitivity_reason"] = item.get("metadata", {}).get("sensitivity_reason", "Sensitive debate")
        else:
            merged_by_id[item_id] = item
            if url:
                url_to_id[url] = item_id
            title_hash_to_id[title_hash] = item_id

    return list(merged_by_id.values())


class TrendCacheManager:
    """
    Manages atomic persistence, retrieval, corruption recovery, and 48-hour retention
    for discovered trends in data/trends_cache.json using atomic JSON helpers.
    """

    def __init__(self, cache_file: Optional[Union[str, Path]] = None):
        if cache_file:
            self.cache_file = Path(cache_file)
        else:
            self.cache_file = Path(__file__).resolve().parent.parent / "data" / "trends_cache.json"

    def _default_cache(self) -> Dict[str, Any]:
        return {
            "metadata": {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_trends": 0,
                "active_trends": 0,
                "sensitive_trends": 0,
                "retention_hours": 48
            },
            "trends": []
        }

    def load_cache(self) -> Dict[str, Any]:
        """
        Safely reads the trends cache.
        If missing: returns default structure.
        If corrupted: backs up corrupted file and returns fresh default structure.
        """
        if not self.cache_file.exists():
            return self._default_cache()

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "trends" in data and isinstance(data["trends"], list):
                    return data
                return self._default_cache()
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            corrupt_backup = self.cache_file.with_name(f"{self.cache_file.name}.corrupt.{int(time.time())}")
            try:
                self.cache_file.rename(corrupt_backup)
            except Exception:
                pass
            print(f"[TrendHunter] Warning: corrupted trends cache detected. Backed up to {corrupt_backup.name}.")
            return self._default_cache()
        except OSError as e:
            print(f"[TrendHunter] Warning: could not read cache file ({e}). Using in-memory fallback.")
            return self._default_cache()

    def save_cache(self, data: Dict[str, Any]) -> bool:
        """
        Saves cache data atomically via src.x_state.atomic_write_json.
        """
        try:
            trends = data.get("trends", [])
            data.setdefault("metadata", {})
            data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
            data["metadata"]["total_trends"] = len(trends)
            data["metadata"]["active_trends"] = len(trends)
            data["metadata"]["sensitive_trends"] = sum(1 for t in trends if t.get("is_sensitive", False))
            data["metadata"]["retention_hours"] = 48

            atomic_write_json(self.cache_file, data)
            return True
        except Exception as e:
            print(f"[TrendHunter] Error saving trend cache to {self.cache_file}: {e}")
            return False

    def prune_expired(self, max_age_hours: float = 48.0) -> int:
        """
        Removes trends where discovered_at is older than max_age_hours.
        Returns the number of pruned items.
        """
        data = self.load_cache()
        trends = data.get("trends", [])
        now_dt = datetime.now(timezone.utc)

        valid_trends = []
        pruned_count = 0
        for t in trends:
            disc_str = t.get("discovered_at")
            if not disc_str:
                valid_trends.append(t)
                continue
            try:
                disc_dt = datetime.fromisoformat(disc_str.replace("Z", "+00:00"))
                age_hours = (now_dt - disc_dt).total_seconds() / 3600.0
                if age_hours <= max_age_hours:
                    valid_trends.append(t)
                else:
                    pruned_count += 1
            except Exception:
                valid_trends.append(t)

        if pruned_count > 0:
            data["trends"] = valid_trends
            self.save_cache(data)
        return pruned_count

    def update_trends(self, new_trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merges new trends into existing cache, prunes expired trends, deduplicates,
        ranks deterministically, and saves to data/trends_cache.json.
        """
        self.prune_expired(max_age_hours=48.0)
        data = self.load_cache()
        existing_trends = data.get("trends", [])

        combined = deduplicate_trends(existing_trends + new_trends)
        ranked = rank_trends(combined)

        data["trends"] = ranked
        self.save_cache(data)
        return ranked

    def get_trends(
        self,
        category: Optional[str] = None,
        include_sensitive: bool = True,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Returns cached trends matching filter criteria.
        """
        data = self.load_cache()
        trends = data.get("trends", [])
        filtered = []
        for t in trends:
            if not include_sensitive and t.get("is_sensitive", False):
                continue
            if category and t.get("category") != category:
                continue
            filtered.append(t)
            if len(filtered) >= limit:
                break
        return filtered


class TrendHunter:
    """Discovers viral, debated, and breaking topics across the web 100% free with fast RSS & APIs."""

    def __init__(self, cache_file: Optional[Union[str, Path]] = None):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        self.cache = TrendCacheManager(cache_file)

    def get_google_trends(self, geo: str = "IN") -> List[Dict[str, Any]]:
        """Pulls top real-time trending spikes from Google Trends RSS (Default: India for explosive reach)."""
        trends = []
        for region in [geo, "US"]:
            try:
                url = f"https://trends.google.com/trending/rss?geo={region}"
                feed = feedparser.parse(url)
                for entry in feed.entries[:6]:
                    approx_traffic = getattr(entry, "ht_approx_traffic", "Trending Spike")
                    raw = {
                        "title": entry.title,
                        "summary": getattr(entry, "summary", entry.title),
                        "traffic": approx_traffic,
                        "category": "breaking_news",
                        "published_parsed": getattr(entry, "published_parsed", None)
                    }
                    normalized = normalize_trend_item(raw, source=f"Google Trends ({region})", default_category="breaking_news")
                    if normalized:
                        trends.append(normalized)
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
                        raw = {
                            "title": item.get("title", ""),
                            "summary": item.get("title", ""),
                            "comments_count": item.get("descendants", 0),
                            "score": item.get("score", 0),
                            "url": item.get("url", ""),
                            "time": item.get("time"),
                            "category": "ai_tech"
                        }
                        normalized = normalize_trend_item(raw, source="HackerNews", default_category="ai_tech")
                        if normalized:
                            news.append(normalized)
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
                    raw = {
                        "title": entry.title,
                        "summary": getattr(entry, "summary", entry.title)[:200],
                        "url": getattr(entry, "link", ""),
                        "traffic": "Breaking",
                        "category": category,
                        "published_parsed": getattr(entry, "published_parsed", None)
                    }
                    normalized = normalize_trend_item(raw, source=source_name, default_category=category)
                    if normalized:
                        items.append(normalized)
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
                "traffic": "High Signal AI",
                "category": "ai_tech",
                "url": "https://app.neubench.workers.dev/"
            },
            {
                "title": "Real-World TTFT & Throughput Benchmarks across Major LLM Hosted Endpoints",
                "summary": "NeuBench speed testing shows real-world token throughput variances up to 40% across hosted provider APIs.",
                "company": "NeuBench",
                "traffic": "High Signal AI",
                "category": "ai_tech",
                "url": "https://app.neubench.workers.dev/"
            },
            {
                "title": "Quantized FP8 vs Dense Weights for Autonomous Coding Agents",
                "summary": "NeuBench evaluations analyze benchmark accuracy drop versus inference acceleration on local and cloud models.",
                "company": "NeuBench",
                "traffic": "High Signal AI",
                "category": "ai_tech",
                "url": "https://app.neubench.workers.dev/"
            },
            {
                "title": "LLM API Outage Frequency & Degradation Index",
                "summary": "NeuBench monitoring tracks endpoint reliability and error rates across top frontier intelligence providers.",
                "company": "NeuBench",
                "traffic": "High Signal AI",
                "category": "ai_tech",
                "url": "https://app.neubench.workers.dev/"
            }
        ]
        results = []
        for c in curated[:limit]:
            normalized = normalize_trend_item(c, source="NeuBench Live Telemetry", default_category="ai_tech")
            if normalized:
                results.append(normalized)
        return results

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
                        raw = {
                            "title": title,
                            "summary": summary[:300],
                            "traffic": "Frontier AI Research",
                            "category": "frontier_paper",
                            "url": f"https://huggingface.co/papers/{p.get('id', '')}",
                            "published_at": p.get("publishedAt")
                        }
                        normalized = normalize_trend_item(raw, source="Hugging Face Daily Papers", default_category="frontier_paper")
                        if normalized:
                            papers.append(normalized)
        except Exception as e:
            print(f"[TrendHunter] Hugging Face Daily Papers error: {e}")
        return papers

    def get_curated_trending_topics(self, use_cache: bool = True, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Discovers, normalizes, deduplicates, and deterministically ranks trending topics
        across all live sources, persisting them to data/trends_cache.json.
        """
        if use_cache and not refresh:
            cached = self.cache.get_trends(limit=30)
            if cached:
                return cached

        all_trends: List[Dict[str, Any]] = []
        try:
            all_trends.extend(self.get_neubench_stories())
        except Exception as e:
            print(f"[TrendHunter] NeuBench stories error: {e}")

        try:
            all_trends.extend(self.get_huggingface_daily_papers())
        except Exception as e:
            print(f"[TrendHunter] Hugging Face papers error: {e}")

        try:
            all_trends.extend(self.get_tech_news())
        except Exception as e:
            print(f"[TrendHunter] Tech news error: {e}")

        try:
            all_trends.extend(self.get_breaking_rss())
        except Exception as e:
            print(f"[TrendHunter] Breaking RSS error: {e}")

        try:
            all_trends.extend(self.get_google_trends(geo="IN"))
        except Exception as e:
            print(f"[TrendHunter] Google Trends error: {e}")

        deduped = deduplicate_trends(all_trends)
        ranked = rank_trends(deduped)
        self.cache.update_trends(ranked)
        return ranked

    def get_candidate_trends(
        self,
        platform: str = "x",
        limit: int = 15,
        include_sensitive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Returns top-ranked candidate trends from cache, or fetches fresh if cache is empty.
        Filters by sensitive topics if include_sensitive is False.
        """
        cached = self.cache.get_trends(include_sensitive=include_sensitive, limit=limit)
        if not cached:
            self.get_curated_trending_topics(use_cache=False, refresh=True)
            cached = self.cache.get_trends(include_sensitive=include_sensitive, limit=limit)
        return cached

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
        try:
            from src.ai_generator import AIGenerator
            gen = AIGenerator()
            recent = list(used_topics)[-30:] if used_topics else []
            topic = gen.ideate_autonomous_tech_topic(target_audience="ai_curious", recent_topics=recent)
            if topic and topic.get("title"):
                return topic
        except Exception:
            pass
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



    def get_educational_concepts(self, used_topics=None):
        try:
            from src.ai_generator import AIGenerator
            gen = AIGenerator()
            recent = list(used_topics)[-30:] if used_topics else []
            topic = gen.ideate_autonomous_tech_topic(content_format="terminology_demystified", recent_topics=recent)
            if topic and topic.get("title"):
                return [topic]
        except Exception:
            pass
        concepts = [
            {
                "title": "Git Rebase vs. Git Merge",
                "category": "SOFTWARE ENGINEERING",
                "concept_a": {
                    "name": "Git Rebase",
                    "how_it_works": "Rewrites commit history by replaying your branch commits directly on top of the target branch tip. Generates brand new commit hashes.",
                    "analogy": "Like taking your chapter out of a book and pasting it at the very end of the latest draft so it looks like you wrote it today.",
                    "best_for": "Local feature branches before opening a PR to maintain a spotless linear history."
                },
                "concept_b": {
                    "name": "Git Merge",
                    "how_it_works": "Preserves full historical timeline by combining two branch heads with a dedicated 2-parent 'merge commit'. Never alters existing commits.",
                    "analogy": "Like two independent rivers flowing together into one bigger river - you clearly see where both streams came from.",
                    "best_for": "Merging finished feature branches or PRs into main/master to retain authentic historical audit trails."
                },
                "school_analogy": "Merge joins two independent paths and records that a merge happened. Rebase rewrites your timeline as if your changes were made on top of the newest code.",
                "pro_nuance": "GOLDEN RULE: Never rebase a public branch that other developers have pulled! Rewriting shared commit hashes forces collaborators into merge conflict hell.",
                "tradeoff_table": [
                    ("History Structure", "Linear & Clean", "Branched & Non-Linear"),
                    ("Commit Hashes", "Rewritten (New SHAs)", "100% Preserved"),
                    ("Merge Commit", "None created", "Creates 2-parent commit"),
                    ("Public Branch Safe", "NO (Breaks coworkers)", "YES (Completely safe)")
                ],
                "golden_rule": "Rebase locally to clean up your PR; Merge into main to preserve history."
            },
            {
                "title": "Git Merge vs. Squash vs. Cherry-Pick",
                "category": "SOFTWARE ENGINEERING",
                "concept_a": {
                    "name": "Squash and Merge",
                    "how_it_works": "Condenses 30 'wip', 'fix typo', 'oops' commits from a feature branch into a single clean commit on main.",
                    "analogy": "Writing 15 rough drafts on scrap paper, but only turning in the final polished essay to the teacher.",
                    "best_for": "Feature PRs where internal iteration noise does not matter for main branch history."
                },
                "concept_b": {
                    "name": "Cherry-Pick",
                    "how_it_works": "Selectively applies the exact changes from one specific commit hash onto your current branch without merging the whole branch.",
                    "analogy": "Reaching into a box of assorted donuts and plucking out only the single chocolate one without taking the box.",
                    "best_for": "Hotfixing production by pulling a bugfix from development without deploying unreleased features."
                },
                "school_analogy": "Standard merge keeps all 50 commits. Squash condenses them into 1. Cherry-pick pulls just 1 specific commit from another branch.",
                "pro_nuance": "Squashing obscures individual author contributions if multiple people pushed to one branch. Use Squash for single-author PRs.",
                "tradeoff_table": [
                    ("Commit Count", "Single condensed commit", "Exact selected commit only"),
                    ("Context Carried", "Combines all branch changes", "Only changes in that specific commit"),
                    ("History Noise", "Zero noise on main", "Zero noise from other branch commits"),
                    ("Best Use Case", "Closing feature PRs", "Critical hotfixes to release branches")
                ],
                "golden_rule": "Squash PRs to keep main clean; Cherry-pick to backport urgent hotfixes."
            },
            {
                "title": "LLM vs. SLM (Small Language Models)",
                "category": "AI & MACHINE LEARNING",
                "concept_a": {
                    "name": "Frontier LLM (70B-671B+)",
                    "how_it_works": "Massive parameter networks (DeepSeek R1, Claude 3.5, Llama 3.3 70B) with deep emergent reasoning across complex ambiguous tasks.",
                    "analogy": "A world-class university professor with encyclopedic knowledge across every domain.",
                    "best_for": "Complex reasoning, autonomous code generation, multifaceted research synthesis."
                },
                "concept_b": {
                    "name": "Small Language Model (SLM, 1B-8B)",
                    "how_it_works": "Highly distilled models (Phi-4, Llama 3.2 3B, Gemma 2 9B) optimized to run locally on mobile, edge devices, or single GPUs.",
                    "analogy": "A sharp, specialized medical technician who does one specific job with blazing speed and zero cloud bills.",
                    "best_for": "Structured JSON extraction, edge device inference, real-time classification, local privacy."
                },
                "school_analogy": "An LLM is a giant encyclopedic brain that requires a data center. An SLM is a compact pocket assistant that runs directly on your laptop or phone.",
                "pro_nuance": "In production, 80% of business tasks are simple classification or extraction. Routing those to an SLM drops inference bills by 95% and latency to under 50ms.",
                "tradeoff_table": [
                    ("Memory / VRAM", "140GB+ (Multi-GPU)", "4GB - 16GB (Consumer GPU/Laptop)"),
                    ("Latency (TTFT)", "200ms - 800ms", "15ms - 50ms (Blazing fast)"),
                    ("Cost per 1M Tokens", "$2.00 - $15.00+", "$0.05 - $0.20 (or free locally)"),
                    ("Complex Reasoning", "State of the art", "Moderate (Requires strict prompting)")
                ],
                "golden_rule": "Route simple queries to an SLM; escalate complex reasoning to a frontier LLM."
            },
            {
                "title": "RAG vs. Fine-Tuning",
                "category": "AI ARCHITECTURE",
                "concept_a": {
                    "name": "RAG (Retrieval-Augmented Generation)",
                    "how_it_works": "Fetches external documents from a vector database and inserts them into the prompt at runtime as an open-book reference.",
                    "analogy": "Taking an open-book exam where you can look up the exact company policy in an indexed textbook.",
                    "best_for": "Dynamic enterprise data, preventing hallucinations, providing citations, frequent updates."
                },
                "concept_b": {
                    "name": "Fine-Tuning",
                    "how_it_works": "Updates the internal neural network weights using domain-specific dataset pairs, teaching the model new styles, formats, or tone.",
                    "analogy": "Spending 3 months practicing a foreign dialect so you naturally speak with that specific accent.",
                    "best_for": "Custom output formats (e.g. strict SQL/JSON syntax), domain vocabulary, niche styling."
                },
                "school_analogy": "RAG gives the AI an open book to read facts. Fine-tuning teaches the AI a new writing style or specialized skill.",
                "pro_nuance": "Never fine-tune to teach a model facts! Models easily forget or hallucinate factual updates. Use RAG for knowledge, fine-tuning for style and form.",
                "tradeoff_table": [
                    ("Knowledge Updates", "Instant (Update database)", "Slow (Requires retraining & deploy)"),
                    ("Hallucination Risk", "Very Low (Grounded in context)", "Moderate to High"),
                    ("Setup Cost", "Low (Embeddings & Vector DB)", "High (GPU training & curation)"),
                    ("Citations / Audit", "100% Verifiable source links", "Opaque neural memory")
                ],
                "golden_rule": "Use RAG for facts and knowledge; use Fine-Tuning for style, tone, and strict syntax."
            },
            {
                "title": "REST vs. gRPC vs. GraphQL",
                "category": "API ARCHITECTURE",
                "concept_a": {
                    "name": "gRPC (HTTP/2 + Protobuf)",
                    "how_it_works": "Binary protocol buffers over multiplexed HTTP/2 streams with strongly typed RPC contracts and bidirectional streaming.",
                    "analogy": "A private dedicated fiber optic line speaking high-speed binary Morse code between two military bases.",
                    "best_for": "Internal microservice-to-microservice communication where sub-millisecond latency is vital."
                },
                "concept_b": {
                    "name": "REST and GraphQL",
                    "how_it_works": "REST exposes resource endpoints over JSON/HTTP. GraphQL allows clients to request exact fields across a unified schema graph.",
                    "analogy": "A restaurant menu: REST makes you order fixed combo meals; GraphQL lets you build a custom bowl ingredient by ingredient.",
                    "best_for": "Public APIs, mobile clients, web frontends needing human-readable JSON."
                },
                "school_analogy": "REST is standard postal mail with letters. GraphQL is ordering custom items from a buffet. gRPC is a supercomputer pipeline between servers.",
                "pro_nuance": "gRPC binary payloads are up to 7x smaller and 10x faster to serialize than JSON, but impossible for browsers to debug natively without tooling.",
                "tradeoff_table": [
                    ("Serialization", "Binary Protobuf (Fastest)", "Textual JSON (Human readable)"),
                    ("Transport", "HTTP/2 Multiplexed", "HTTP/1.1 or HTTP/2"),
                    ("Browser Support", "Requires gRPC-Web proxy", "Native in all browsers"),
                    ("Best Environment", "Internal Microservices", "Public Web & Mobile APIs")
                ],
                "golden_rule": "Use gRPC for high-throughput internal backend services; use REST/GraphQL for frontend APIs."
            },
            {
                "title": "Docker vs. Kubernetes vs. Podman",
                "category": "DEVOPS & CLOUD",
                "concept_a": {
                    "name": "Docker & Podman (Containerization)",
                    "how_it_works": "Packages application code and all OS dependencies into isolated, reproducible container images running on a shared OS kernel.",
                    "analogy": "Standardized shipping containers that can be loaded onto any ship, train, or truck in the world without unpacking.",
                    "best_for": "Local development, packaging microservices, daemonless rootless containers (Podman)."
                },
                "concept_b": {
                    "name": "Kubernetes (K8s Orchestration)",
                    "how_it_works": "Automates deployment, scaling, health checks, load balancing, and failover across clusters of hundreds of containerized servers.",
                    "analogy": "The master harbor master orchestrating 500 ships, cranes, and schedules simultaneously across 10 global ports.",
                    "best_for": "Production cloud deployments requiring auto-scaling, rolling updates, and self-healing."
                },
                "school_analogy": "Docker is the shipping container. Kubernetes is the cargo ship fleet and harbor management system.",
                "pro_nuance": "Do not jump to Kubernetes if you have 3 containers! A simple Docker Compose or single VM setup is 100x easier to maintain for early startups.",
                "tradeoff_table": [
                    ("Primary Role", "Package & Run a Container", "Orchestrate & Scale Clusters"),
                    ("Complexity", "Low (Simple Dockerfile)", "High (YAML, Ingress, Helm, CNI)"),
                    ("Auto-Healing", "Restarts container locally", "Reschedules pods across healthy nodes"),
                    ("When to Adopt", "Day 1 of any project", "When scaling across multiple nodes")
                ],
                "golden_rule": "Build with Docker/Podman from Day 1; adopt Kubernetes only when multi-node orchestration is mandatory."
            },
            {
                "title": "B-Trees vs. Hash Indexes",
                "category": "DATABASE INTERNALS",
                "concept_a": {
                    "name": "B-Tree Index (Default in Postgres/MySQL)",
                    "how_it_works": "Self-balancing multi-way search tree that keeps keys sorted in pages, enabling O(log N) lookups for both equality and range scans.",
                    "analogy": "A library catalog where books are organized alphabetically by author - you can find 'Smith' or browse everyone from 'S' to 'T'.",
                    "best_for": "General database columns, date ranges (created_at > '2026-01-01'), sorting, inequalities."
                },
                "concept_b": {
                    "name": "Hash Index",
                    "how_it_works": "Passes keys through a hash function into a bucket table for theoretical O(1) instant pointer resolution.",
                    "analogy": "A coat check ticket number: give the number, get your exact jacket instantly. But you cannot ask for all coats between ticket 40 and 60.",
                    "best_for": "Pure equality checks (WHERE user_id = 'abc') in memory-heavy key-value systems."
                },
                "school_analogy": "B-Trees are like alphabetized phone books. Hash indexes are coat checks (only exact matches).",
                "pro_nuance": "Never use a Hash Index on columns where you query with '>', '<', 'BETWEEN', or 'ORDER BY' - hash indexes have zero concept of ordering!",
                "tradeoff_table": [
                    ("Equality Lookups (=)", "O(log N) - Blazing fast", "O(1) - Instant"),
                    ("Range Queries", "YES (Ordered scan)", "NO (Requires full table scan)"),
                    ("Sorting (ORDER BY)", "YES (Zero cost traversal)", "NO (Requires external sort)"),
                    ("Default Choice", "YES (Postgres / MySQL default)", "Specialized only")
                ],
                "golden_rule": "Stick to B-Trees for 99% of relational columns; use Hash only for pure memory equality lookups."
            },
            {
                "title": "Event Loop: Node.js & Python Asyncio",
                "category": "CONCURRENCY & RUNTIMES",
                "concept_a": {
                    "name": "Event-Driven Non-Blocking I/O",
                    "how_it_works": "A single main thread continuously polls an event queue. When an I/O operation starts, it offloads to OS kernel (epoll/kqueue) and moves on to the next request without blocking.",
                    "analogy": "A single waiter in a restaurant who takes your order, hands it to the kitchen, and immediately takes the next table's order without waiting at the stove.",
                    "best_for": "High-concurrency network servers, WebSockets, API gateways handling 100k simultaneous idle connections."
                },
                "concept_b": {
                    "name": "Multi-Threaded Blocking I/O",
                    "how_it_works": "Spawns a dedicated OS thread per incoming request. The thread sleeps while waiting for the database response.",
                    "analogy": "A restaurant where each table gets their own waiter who stands frozen at the kitchen counter until your pasta is cooked.",
                    "best_for": "CPU-bound heavy compute tasks (video transcoding, matrix math, encryption)."
                },
                "school_analogy": "Instead of hiring 1,000 waiters who stand idle waiting for food, one super-fast waiter coordinates everything while the kitchen cooks.",
                "pro_nuance": "The fatal weakness of the event loop: CPU-intensive operations (heavy loops, JSON parsing 500MB) block the single thread, freezing all other 10,000 users!",
                "tradeoff_table": [
                    ("Memory Footprint", "Tiny (Single stack, event queue)", "Heavy (~2MB-8MB per OS thread)"),
                    ("I/O Concurrency", "Massive (100k+ connections)", "Limited by OS thread limits"),
                    ("CPU Bound Tasks", "Terrible (Blocks whole loop)", "Great (Uses all CPU cores)"),
                    ("Debugging Complexity", "Async stack traces", "Race conditions & deadlocks")
                ],
                "golden_rule": "Use the Event Loop for high-throughput I/O servers; offload heavy CPU computation to worker threads or processes."
            },
            {
                "title": "TCP vs. UDP",
                "category": "NETWORKING",
                "concept_a": {
                    "name": "TCP (Transmission Control Protocol)",
                    "how_it_works": "Connection-oriented with a 3-way handshake (SYN, SYN-ACK, ACK). Guarantees in-order packet delivery, retransmits lost packets, and manages congestion.",
                    "analogy": "Certified registered mail: you sign a receipt confirming you received page 1 before page 2 is handed over.",
                    "best_for": "Web browsing (HTTP), banking, email, file transfers where dropping a single byte corrupts the file."
                },
                "concept_b": {
                    "name": "UDP (User Datagram Protocol)",
                    "how_it_works": "Connectionless fire-and-forget datagrams. No handshakes, zero retransmissions, zero congestion delay.",
                    "analogy": "A live radio broadcast: if static garbles half a second of audio, the station keeps playing - they don't pause the song to replay the word.",
                    "best_for": "Real-time multiplayer games, live video calls (WebRTC), DNS lookups, audio streaming."
                },
                "school_analogy": "TCP is a phone call where you confirm 'Did you hear me?'. UDP is speaking through a megaphone to a crowd without waiting for a reply.",
                "pro_nuance": "HTTP/3 runs on QUIC, which builds reliability on top of UDP to eliminate TCP head-of-line blocking while maintaining zero packet loss!",
                "tradeoff_table": [
                    ("Reliability", "100% Guaranteed & In-Order", "No guarantee (Packets can drop)"),
                    ("Connection Overhead", "3-Way Handshake + Teardown", "Zero handshake (Send immediately)"),
                    ("Speed & Latency", "Higher overhead (Retransmissions)", "Blazing fast minimal latency"),
                    ("Header Size", "20-60 Bytes", "8 Bytes (Minimal packet weight)")
                ],
                "golden_rule": "Use TCP when accuracy is paramount; use UDP/QUIC when real-time latency beats perfection."
            },
            {
                "title": "Monolith vs. Microservices",
                "category": "SYSTEM DESIGN",
                "concept_a": {
                    "name": "Modular Monolith",
                    "how_it_works": "Entire codebase lives in a single repository and deploys as a single unified service, sharing in-memory function calls and a single database.",
                    "analogy": "A single Swiss Army Knife where knife, scissors, and bottle opener are all in one solid handle.",
                    "best_for": "Startups, small-to-mid teams, early product market fit, simple CI/CD pipelines."
                },
                "concept_b": {
                    "name": "Microservices",
                    "how_it_works": "Splits domain boundaries into dozens of independent services communicating over network RPCs (REST, gRPC) with independent databases.",
                    "analogy": "A construction crew of 15 independent subcontracted companies that must constantly call each other on cell phones to build a house.",
                    "best_for": "Large organizations (100+ engineers) where independent team release velocity outweighs network overhead."
                },
                "school_analogy": "A monolith is one building housing all departments. Microservices are 20 separate buildings across town that have to courier documents back and forth.",
                "pro_nuance": "Microservices solve organizational scaling (coordinating 500 engineers), not technical scaling. If your team has fewer than 30 engineers, microservices create 10x more latency and devops pain.",
                "tradeoff_table": [
                    ("Deployment Complexity", "Single command deployment", "Dozens of CI/CD pipelines & Docker images"),
                    ("Data Consistency", "ACID transactions in 1 DB", "Eventual consistency & Saga patterns"),
                    ("Network Latency", "Zero (In-memory function call)", "High (Network hops across services)"),
                    ("Team Autonomy", "Shared deployment queue", "Independent team deployment cycles")
                ],
                "golden_rule": "Start with a clean modular monolith; break out microservices only when team coordination demands it."
            }
        ]
        import random
        if used_topics:
            used_set = set(t.lower().strip() for t in used_topics)
            unseen = [item for item in concepts if item.get('title', '').lower().strip() not in used_set]
            if unseen:
                return unseen
        return concepts

    def get_comparison_topics(self, used_topics=None) -> List[Dict[str, Any]]:
        """Return dynamic technical and architectural comparison (versus) topics."""
        try:
            from src.ai_generator import AIGenerator
            gen = AIGenerator()
            recent = list(used_topics)[-30:] if used_topics else []
            topic = gen.ideate_autonomous_tech_topic(content_format="versus_comparison", recent_topics=recent)
            if topic and topic.get("title"):
                return [topic]
        except Exception:
            pass
        comparisons = [
            {"title": "HashMap vs. HashSet", "concept_a": "HashMap", "concept_b": "HashSet", "category": "DATA STRUCTURES", "summary": "Key-value associative mapping vs unique set membership under the hood."},
            {"title": "ArrayList vs. LinkedList", "concept_a": "ArrayList", "concept_b": "LinkedList", "category": "DATA STRUCTURES", "summary": "Contiguous memory cache locality vs pointer node allocation overhead."},
            {"title": "Stack vs. Queue", "concept_a": "Stack (LIFO)", "concept_b": "Queue (FIFO)", "category": "DATA STRUCTURES", "summary": "Call stack recursion state vs message pipeline asynchronous buffering."},
            {"title": "REST vs. GraphQL vs. gRPC", "concept_a": "REST / JSON", "concept_b": "gRPC / Protobuf", "category": "NETWORK PROTOCOLS", "summary": "HTTP/1.1 stateless ubiquity vs HTTP/2 binary multiplexed RPC throughput."},
            {"title": "SQL vs. NoSQL (PostgreSQL vs. MongoDB)", "concept_a": "PostgreSQL (ACID / Relational)", "concept_b": "MongoDB (Document / Distributed)", "category": "DATABASE SYSTEMS", "summary": "Strict relational schemas & WAL logging vs horizontal sharded document flexibility."},
            {"title": "RAG vs. Fine-Tuning", "concept_a": "Retrieval-Augmented Generation", "concept_b": "Supervised Fine-Tuning", "category": "AI INFRASTRUCTURE", "summary": "Dynamic vector search groundings vs parametric weight specialization."},
            {"title": "AI Agents vs. Traditional Automation", "concept_a": "Autonomous AI Agents", "concept_b": "Deterministic Workflows", "category": "SYSTEMS ARCHITECTURE", "summary": "Probabilistic non-linear tool calling vs deterministic rigid pipeline reliability."},
            {"title": "MCP vs. REST API", "concept_a": "Model Context Protocol", "concept_b": "Traditional REST APIs", "category": "SYSTEMS ARCHITECTURE", "summary": "Standardized client-host agent tooling vs point-to-point bespoke endpoint contracts."},
            {"title": "LLM vs. SLM (Small Language Models)", "concept_a": "Frontier LLM (70B+)", "concept_b": "Small Language Model (1B-8B)", "category": "AI & MACHINE LEARNING", "summary": "Deep multi-domain reasoning in cloud clusters vs quantized local edge latency."},
            {"title": "Docker vs. Virtual Machines", "concept_a": "Docker Containers", "concept_b": "Hardware Virtual Machines", "category": "SYSTEMS ARCHITECTURE", "summary": "Shared OS kernel namespace isolation vs hypervisor hardware emulation."},
            {"title": "Monolith vs. Microservices", "concept_a": "Modular Monolith", "concept_b": "Distributed Microservices", "category": "SYSTEMS ARCHITECTURE", "summary": "In-process memory call simplicity vs network serialized latency and distributed state."},
            {"title": "Kafka vs. RabbitMQ", "concept_a": "Apache Kafka", "concept_b": "RabbitMQ", "category": "DISTRIBUTED SYSTEMS", "summary": "Distributed partitioned commit log replay vs AMQP smart broker push queueing."},
            {"title": "Redis vs. Memcached", "concept_a": "Redis", "concept_b": "Memcached", "category": "CACHING & MEMORY", "summary": "Multi-data-structure persistence & pub/sub vs pure multithreaded key-value caching."},
            {"title": "Optimistic vs. Pessimistic Locking", "concept_a": "Optimistic Locking", "concept_b": "Pessimistic Locking", "category": "DATABASE CONCURRENCY", "summary": "Version check conflict retries vs row-level lock serialization under high write contention."},
            {"title": "TCP vs. UDP", "concept_a": "TCP (Transmission Control Protocol)", "concept_b": "UDP (User Datagram Protocol)", "category": "NETWORKING", "summary": "3-way handshake & guaranteed ordered delivery vs connectionless zero-overhead datagram streaming."},
            {"title": "Event-Driven vs. Request-Driven Architecture", "concept_a": "Event-Driven (Pub/Sub)", "concept_b": "Request-Driven (RPC / REST)", "category": "DISTRIBUTED SYSTEMS", "summary": "Asynchronous decoupled event streams vs synchronous blocking call topologies."}
        ]
        if used_topics:
            used_set = {str(t).lower().strip() for t in used_topics}
            unseen = [item for item in comparisons if item.get('title', '').lower().strip() not in used_set]
            if unseen:
                return unseen
        return comparisons

    def get_x_unfiltered_topics(self):
        import random
        unfiltered = [
            {'title': 'Election season promises vs reality', 'context': 'Politicians promising free electricity, bullet trains, and zero taxes while your neighborhood road has been under construction since the Mughal empire.'},
            {'title': 'Income tax vs public infrastructure', 'context': 'Paying 35% of your income in taxes and then having to buy private water, private power backup, private security, and medical insurance.'},
            {'title': 'Free speech hypocrisy on social media', 'context': 'Everyone champions free speech until someone tweets an opinion they disagree with, at which point it is suddenly hate speech and treason.'},
            {'title': 'Politicians on social media PR teams', 'context': '75-year-old politicians with PR agencies tweeting Gen Z slang like no cap and we cooked while drafting anti-internet laws.'},
            {'title': 'Religious dogmatism vs basic human decency', 'context': 'People who will fiercely fight you on Twitter over religious rituals but casually throw garbage onto the street and cut traffic signals.'},
            {'title': 'Astrology and Kundali in the age of quantum computing', 'context': 'Building space stations and AI agents while Indian parents still reject marriage proposals because Mars was in the 7th house in 1998.'},
            {'title': 'Moral policing uncle-aunt networks', 'context': 'Society uncles having zero opinion on corruption or pollution but having a 3-hour emergency society meeting because a girl wore shorts near the gate.'},
            {'title': 'AI will replace coders vs Indian IT bodyshopping', 'context': 'Silicon Valley says AI will replace software engineers. Indian IT companies just assigned 4,000 freshers to maintain a 25-year-old COBOL mainframe for an insurance client in Ohio.'},
            {'title': 'Tech CEO return-to-office mandates', 'context': 'Tech CEOs selling cloud collaboration software worth billions, then forcing their own engineers into office cubicles because collaboration happens at the water cooler.'},
            {'title': 'Startup founders preaching hustle on LinkedIn', 'context': 'Startup founder with $5M in VC funding lecturing 22-year-olds on 80-hour workweeks while their burn rate is $200k/month on artisanal oat milk.'},
            {'title': 'Scrum master daily rituals', 'context': 'The corporate phenomenon of having 6 project managers, 2 scrum masters, and 1 developer who actually writes code.'},
            {'title': 'The AI bubble and pitch deck madness', 'context': 'Putting a $50 OpenAI API wrapper on a database and calling yourself a Pre-Seed Autonomous Enterprise Agent Platform with a $20M valuation.'},
            {'title': 'Middle-class investment paranoia', 'context': 'Middle class uncle putting all money in fixed deposits yielding 6% while inflation is 8%, but warning you that buying a $20 book is financial recklessness.'},
            {'title': 'Gym bros vs reality', 'context': 'Taking 4 scoops of pre-workout, wearing $300 gym gear, and then doing 3 bicep curls and spending 45 minutes on Instagram reels on the bench press.'},
            {'title': 'Restaurant service charge entitlement', 'context': 'Restaurants charging 10% service charge, 5% GST, 18% AC tax, and then the waiter stares into your soul waiting for a cash tip.'}
        ]
        try:
            spikes = self.get_google_trends(geo='IN') + self.get_google_trends(geo='US')
            for sp in spikes:
                unfiltered.append({'title': sp.get('title', ''), 'context': f'Real-time trending debate: {sp.get("title", "")}'})
        except Exception:
            pass
        random.shuffle(unfiltered)
        return unfiltered

