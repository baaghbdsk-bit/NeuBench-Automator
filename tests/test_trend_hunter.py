import json
import tempfile
import time
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.trend_hunter import (
    DEFAULT_CATEGORY_MULTIPLIERS,
    DEFAULT_SOURCE_WEIGHTS,
    TrendCacheManager,
    TrendHunter,
    calculate_trend_score,
    canonicalize_url,
    deduplicate_trends,
    detect_trend_sensitivity,
    generate_trend_id,
    is_linkedin_relevant_trend,
    normalize_trend_item,
    normalize_trend_title,
    rank_trends,
)


class TrendHunterCoreTests(unittest.TestCase):
    def test_schema_normalization_complete(self):
        raw_entry = {
            "title": "DeepSeek-V3 Open-Weights Benchmark Results",
            "summary": "Full evaluation of latency and reasoning capabilities on NeuBench.",
            "url": "https://app.neubench.workers.dev/stories/123?utm_source=twitter&ref=feed",
            "traffic": "High Signal AI",
            "category": "ai_tech",
            "published_at": "2026-11-06T12:00:00Z",
            "score": 150,
            "comments_count": 42
        }
        item = normalize_trend_item(raw_entry, source="HackerNews", default_category="ai_tech")
        self.assertIsNotNone(item)

        # 1. Check all required schema fields
        expected_fields = [
            "id", "title", "summary", "source", "category",
            "url", "score", "discovered_at", "published_at",
            "is_sensitive", "metadata"
        ]
        for field in expected_fields:
            self.assertIn(field, item, f"Missing required schema field: {field}")

        # 2. Check canonicalized URL (tracking params stripped)
        self.assertEqual(item["url"], "https://app.neubench.workers.dev/stories/123")
        self.assertTrue(item["id"].startswith("tr_"))
        self.assertEqual(item["source"], "HackerNews")
        self.assertEqual(item["category"], "ai_tech")
        self.assertFalse(item["is_sensitive"])
        self.assertEqual(item["metadata"]["hn_score"], 150)
        self.assertEqual(item["metadata"]["hn_comments"], 42)
        self.assertEqual(item["metadata"]["sources_seen"], ["HackerNews"])

    def test_missing_fields_handled_gracefully_without_fabrication(self):
        # Raw entry with minimal data
        raw_minimal = {
            "title": "Quantum Supremacy Update"
        }
        item = normalize_trend_item(raw_minimal, source="Unknown Feed")
        self.assertIsNotNone(item)
        self.assertEqual(item["title"], "Quantum Supremacy Update")
        self.assertEqual(item["summary"], "Quantum Supremacy Update")
        self.assertEqual(item["url"], "")
        self.assertIsNone(item["published_at"])
        self.assertFalse(item["is_sensitive"])
        self.assertNotIn("hn_score", item["metadata"])
        self.assertNotIn("hn_comments", item["metadata"])
        self.assertNotIn("traffic", item["metadata"])

    def test_canonicalize_url_and_title_normalization(self):
        # URL canonicalization
        dirty_url = "https://www.example.com/article/ai-breakthrough/?utm_source=news&utm_medium=rss&ref=xyz#comments"
        cleaned_url = canonicalize_url(dirty_url)
        self.assertEqual(cleaned_url, "https://example.com/article/ai-breakthrough")

        # Title normalization with publisher suffix removal
        raw_title = "ISRO Launches Next-Gen Climate Satellite &amp; Radar - BBC News"
        norm_title = normalize_trend_title(raw_title)
        self.assertEqual(norm_title, "isro launches next-gen climate satellite & radar")

    def test_sensitivity_detection_india_and_communal(self):
        # Sensitive Indian societal/communal debate
        title_sensitive = "Supreme Court hears urgent plea on Waqf Amendment Bill and temple demolition"
        is_sens, reason = detect_trend_sensitivity(title_sensitive, category="breaking_news")
        self.assertTrue(is_sens)
        self.assertIn("Triggered sensitive societal/communal trigger", reason)

        # Standard tech/business discussion
        title_safe = "Infosys and EkStep announce new Digital Public Infrastructure AI framework"
        is_safe, _ = detect_trend_sensitivity(title_safe, category="ai_tech")
        self.assertFalse(is_safe)

    def test_cross_source_deduplication_preserves_attribution(self):
        item_a = {
            "id": "tr_1111",
            "title": "OpenAI reportedly lowers funding target for new round",
            "summary": "Short snippet from TechCrunch.",
            "source": "TechCrunch",
            "category": "ai_tech",
            "url": "https://techcrunch.com/2026/11/06/openai-round",
            "score": 0.0,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "published_at": None,
            "is_sensitive": False,
            "metadata": {"sources_seen": ["TechCrunch"]}
        }

        item_b = {
            "id": "tr_2222",
            "title": "OpenAI reportedly lowers funding target for new round - BBC News",
            "summary": "Longer and more detailed report from BBC World about the latest round valuation.",
            "source": "BBC World",
            "category": "breaking_news",
            "url": "https://techcrunch.com/2026/11/06/openai-round",  # Same canonical reference
            "score": 0.0,
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "published_at": None,
            "is_sensitive": False,
            "metadata": {"sources_seen": ["BBC World"]}
        }

        deduped = deduplicate_trends([item_a, item_b])
        self.assertEqual(len(deduped), 1)

        merged = deduped[0]
        # Verify both sources tracked
        sources = merged["metadata"]["sources_seen"]
        self.assertIn("TechCrunch", sources)
        self.assertIn("BBC World", sources)
        # Verify richer summary preserved
        self.assertIn("Longer and more detailed", merged["summary"])

    def test_deterministic_ranking_reproducible_and_weighted(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        two_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        thirty_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()

        items = [
            {
                "id": "tr_low",
                "title": "Old unknown topic",
                "summary": "...",
                "source": "Unknown Source",
                "category": "breaking_news",
                "url": "https://example.com/old",
                "discovered_at": now_iso,
                "published_at": thirty_hours_ago,
                "is_sensitive": False,
                "metadata": {"sources_seen": ["Unknown Source"]}
            },
            {
                "id": "tr_high",
                "title": "High signal NeuBench telemetry",
                "summary": "...",
                "source": "NeuBench Live Telemetry",
                "category": "frontier_paper",
                "url": "https://app.neubench.workers.dev/1",
                "discovered_at": now_iso,
                "published_at": two_hours_ago,
                "is_sensitive": False,
                "metadata": {"sources_seen": ["NeuBench Live Telemetry", "TechCrunch"]}  # Multi-source
            },
            {
                "id": "tr_mid",
                "title": "HackerNews top story",
                "summary": "...",
                "source": "HackerNews",
                "category": "ai_tech",
                "url": "https://example.com/hn",
                "discovered_at": now_iso,
                "published_at": two_hours_ago,
                "is_sensitive": False,
                "metadata": {"sources_seen": ["HackerNews"], "hn_score": 120}
            }
        ]

        ranked_1 = rank_trends(items)
        # Ranked order should be: tr_high, tr_mid, tr_low
        self.assertEqual(ranked_1[0]["id"], "tr_high")
        self.assertEqual(ranked_1[1]["id"], "tr_mid")
        self.assertEqual(ranked_1[2]["id"], "tr_low")

        # Verify determinism across multiple runs
        ranked_2 = rank_trends(items)
        self.assertEqual([x["id"] for x in ranked_1], [x["id"] for x in ranked_2])
        self.assertEqual([x["score"] for x in ranked_1], [x["score"] for x in ranked_2])


class TrendCachePersistenceTests(unittest.TestCase):
    def test_cache_persistence_atomic_write_and_read(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "trends_cache.json"
            mgr = TrendCacheManager(cache_file)

            # Initially empty
            initial = mgr.load_cache()
            self.assertEqual(len(initial["trends"]), 0)

            # Save trends
            sample_trends = [
                {
                    "id": "tr_test_1",
                    "title": "Bengaluru Tech Hub Infrastructure Expansion",
                    "summary": "Karnataka approves new corridor.",
                    "source": "Google Trends (IN)",
                    "category": "breaking_news",
                    "url": "https://example.com/bengaluru",
                    "score": 10.5,
                    "discovered_at": datetime.now(timezone.utc).isoformat(),
                    "published_at": None,
                    "is_sensitive": False,
                    "metadata": {"sources_seen": ["Google Trends (IN)"]}
                }
            ]
            mgr.update_trends(sample_trends)

            # Verify saved on disk
            self.assertTrue(cache_file.exists())
            loaded = mgr.load_cache()
            self.assertEqual(len(loaded["trends"]), 1)
            self.assertEqual(loaded["trends"][0]["id"], "tr_test_1")
            self.assertEqual(loaded["metadata"]["total_trends"], 1)

    def test_48_hour_expiration_pruning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "trends_cache.json"
            mgr = TrendCacheManager(cache_file)

            now = datetime.now(timezone.utc)
            fresh_time = (now - timedelta(hours=10)).isoformat()
            expired_time = (now - timedelta(hours=50)).isoformat()

            items = [
                {
                    "id": "tr_fresh",
                    "title": "Fresh Topic",
                    "summary": "...",
                    "source": "TechCrunch",
                    "category": "ai_tech",
                    "url": "https://example.com/fresh",
                    "score": 8.0,
                    "discovered_at": fresh_time,
                    "published_at": None,
                    "is_sensitive": False,
                    "metadata": {"sources_seen": ["TechCrunch"]}
                },
                {
                    "id": "tr_expired",
                    "title": "Expired Topic",
                    "summary": "...",
                    "source": "BBC World",
                    "category": "breaking_news",
                    "url": "https://example.com/expired",
                    "score": 7.0,
                    "discovered_at": expired_time,
                    "published_at": None,
                    "is_sensitive": False,
                    "metadata": {"sources_seen": ["BBC World"]}
                }
            ]
            data = mgr._default_cache()
            data["trends"] = items
            mgr.save_cache(data)

            # Prune
            pruned_count = mgr.prune_expired(max_age_hours=48.0)
            self.assertEqual(pruned_count, 1)

            active = mgr.load_cache()["trends"]
            self.assertEqual(len(active), 1)
            self.assertEqual(active[0]["id"], "tr_fresh")

    def test_corrupted_json_recovery(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "trends_cache.json"
            # Write corrupted non-JSON content
            cache_file.write_text("{ this is corrupted invalid json content !!!", encoding="utf-8")

            mgr = TrendCacheManager(cache_file)
            recovered_data = mgr.load_cache()

            # Should not raise exception; should return valid default cache structure
            self.assertIn("trends", recovered_data)
            self.assertEqual(len(recovered_data["trends"]), 0)

            # A corrupted backup file should have been created
            corrupt_files = list(Path(temp_dir).glob("trends_cache.json.corrupt.*"))
            self.assertGreaterEqual(len(corrupt_files), 1)


class TrendHunterMockFeedTests(unittest.TestCase):
    @patch("feedparser.parse")
    @patch("requests.get")
    def test_network_source_failure_gracefully_degrades(self, mock_requests_get, mock_feedparser):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "trends_cache.json"
            hunter = TrendHunter(cache_file=cache_file)

            # Simulate network exceptions across external feeds
            mock_feedparser.side_effect = Exception("DNS Resolution Failure")
            mock_requests_get.side_effect = Exception("Connection Timeout")

            # Must not raise an unhandled exception
            trends = hunter.get_curated_trending_topics(use_cache=False, refresh=True)
            # NeuBench stories are local/curated fallback and still succeed
            self.assertIsInstance(trends, list)
            self.assertGreaterEqual(len(trends), 1)
            self.assertTrue(all(t["source"] == "NeuBench Live Telemetry" for t in trends))

    @patch("feedparser.parse")
    def test_google_trends_india_preserves_attribution_and_normalizes(self, mock_feedparser):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "trends_cache.json"
            hunter = TrendHunter(cache_file=cache_file)

            # Mock feedparser response for Google Trends
            mock_entry = MagicMock()
            mock_entry.title = "ISRO Chandrayaan Mission Update"
            mock_entry.summary = "New telemetry data published on lunar findings."
            mock_entry.ht_approx_traffic = "100K+"
            mock_entry.published_parsed = (2026, 11, 6, 10, 30, 0, 4, 310, 0)

            mock_feed = MagicMock()
            mock_feed.entries = [mock_entry]
            mock_feedparser.return_value = mock_feed

            in_trends = hunter.get_google_trends(geo="IN")
            self.assertEqual(len(in_trends), 2)  # IN and US both queried
            sample = in_trends[0]
            self.assertEqual(sample["title"], "ISRO Chandrayaan Mission Update")
            self.assertEqual(sample["source"], "Google Trends (IN)")
            self.assertEqual(sample["metadata"]["traffic"], "100K+")
            self.assertFalse(sample["is_sensitive"])
            self.assertIsNotNone(sample["published_at"])


class LinkedInTrendRelevanceTests(unittest.TestCase):
    def test_filters_market_consumer_and_non_ai_noise(self):
        self.assertFalse(is_linkedin_relevant_trend("tata motors share price", "", "breaking_news", "Google Trends (IN)"))
        self.assertFalse(is_linkedin_relevant_trend("oneplus coloros 17 update schedule", "", "breaking_news", "Google Trends (IN)"))
        self.assertFalse(is_linkedin_relevant_trend("Kirlian Photography: Building Your Own Equipment", "", "ai_tech", "HackerNews"))
        self.assertFalse(is_linkedin_relevant_trend("WWE Crown Jewel 2026 results", "", "breaking_news", "Google Trends (US)"))
        self.assertFalse(is_linkedin_relevant_trend("Binance CFO is leaving after a $6.3 billion hack", "", "ai_tech", "TechCrunch"))

    def test_keeps_ai_and_engineering_topics(self):
        self.assertTrue(is_linkedin_relevant_trend("KV Cache Eviction Policies for Long-Context Inference", "", "ai_tech", "HackerNews"))
        self.assertTrue(is_linkedin_relevant_trend("B-Tree vs LSM-Tree storage engines", "", "ai_tech", "HackerNews"))
        self.assertTrue(is_linkedin_relevant_trend("Latent context compression for agents", "", "frontier_paper", "Hugging Face Daily Papers"))
        self.assertTrue(is_linkedin_relevant_trend("Frontier reasoning drift and cost per 1M tokens", "", "ai_tech", "NeuBench Live Telemetry"))
        self.assertTrue(is_linkedin_relevant_trend("Kubernetes autoscaling lessons from a production incident", "", "ai_tech", "HackerNews"))

    def test_candidate_trends_platform_filter_applies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "trends_cache.json"
            mgr = TrendCacheManager(cache_file)
            now = datetime.now(timezone.utc).isoformat()
            items = [
                {
                    "id": "tr_stock", "title": "bosch share price", "summary": "",
                    "source": "Google Trends (IN)", "category": "breaking_news",
                    "url": "https://example.com/stock", "score": 12.0,
                    "discovered_at": now, "published_at": None, "is_sensitive": False,
                    "metadata": {"sources_seen": ["Google Trends (IN)"]},
                },
                {
                    "id": "tr_ai", "title": "KV Cache Eviction Policies for Long-Context Inference", "summary": "",
                    "source": "HackerNews", "category": "ai_tech",
                    "url": "https://example.com/ai", "score": 9.0,
                    "discovered_at": now, "published_at": None, "is_sensitive": False,
                    "metadata": {"sources_seen": ["HackerNews"]},
                },
            ]
            mgr.update_trends(items)
            hunter = TrendHunter(cache_file=cache_file)

            linkedin = hunter.get_candidate_trends(platform="linkedin", limit=10)
            self.assertEqual([t["id"] for t in linkedin], ["tr_ai"])

            x_candidates = hunter.get_candidate_trends(platform="x", limit=10)
            self.assertIn("tr_stock", [t["id"] for t in x_candidates])


if __name__ == "__main__":
    unittest.main()
