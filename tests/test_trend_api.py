import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.web.app import app, get_trend_hunter
from src.trend_hunter import TrendCacheManager, TrendHunter


class TrendAPITests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_cache_file = Path(self.temp_dir.name) / "trends_cache.json"
        
        # Point the singleton hunter cache to our temp test file
        self.hunter = get_trend_hunter()
        self.original_cache = self.hunter.cache
        self.hunter.cache = TrendCacheManager(self.temp_cache_file)
        self.client = TestClient(app)

    def tearDown(self):
        self.hunter.cache = self.original_cache
        self.temp_dir.cleanup()

    def _seed_sample_trends(self):
        sample = [
            {
                "id": "tr_ai_1",
                "title": "Frontier Model Benchmarks Live",
                "summary": "NeuBench reveals new latency data.",
                "source": "NeuBench Live Telemetry",
                "category": "ai_tech",
                "url": "https://app.neubench.workers.dev/1",
                "score": 15.2,
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "published_at": "2026-11-06T12:00:00Z",
                "is_sensitive": False,
                "metadata": {"sources_seen": ["NeuBench Live Telemetry"], "traffic": "High Signal AI"}
            },
            {
                "id": "tr_news_sens",
                "title": "Supreme Court stay on contested state policy",
                "summary": "Heated public debate unfolds.",
                "source": "Google Trends (IN)",
                "category": "breaking_news",
                "url": "https://example.com/court",
                "score": 12.0,
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "published_at": None,
                "is_sensitive": True,
                "metadata": {"sources_seen": ["Google Trends (IN)"], "sensitivity_reason": "Court stay"}
            },
            {
                "id": "tr_paper_1",
                "title": "Scaling Laws for Autoregressive Distillation",
                "summary": "Frontier AI research paper analysis.",
                "source": "Hugging Face Daily Papers",
                "category": "frontier_paper",
                "url": "https://huggingface.co/papers/123",
                "score": 14.5,
                "discovered_at": datetime.now(timezone.utc).isoformat(),
                "published_at": "2026-11-06T10:00:00Z",
                "is_sensitive": False,
                "metadata": {"sources_seen": ["Hugging Face Daily Papers"]}
            }
        ]
        self.hunter.cache.update_trends(sample)

    def test_get_trends_empty_cache(self):
        response = self.client.get("/api/trends")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["trends"], [])

    def test_get_trends_cached_and_filtering(self):
        self._seed_sample_trends()

        # 1. Base query - all trends
        res = self.client.get("/api/trends")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["count"], 3)

        # 2. Sensitivity filter (exclude sensitive)
        res_no_sens = self.client.get("/api/trends?include_sensitive=false")
        self.assertEqual(res_no_sens.status_code, 200)
        data_no_sens = res_no_sens.json()
        self.assertEqual(data_no_sens["count"], 2)
        self.assertTrue(all(not t["is_sensitive"] for t in data_no_sens["trends"]))

        # 3. Category filter
        res_cat = self.client.get("/api/trends?category=ai_tech")
        self.assertEqual(res_cat.status_code, 200)
        data_cat = res_cat.json()
        self.assertEqual(data_cat["count"], 1)
        self.assertEqual(data_cat["trends"][0]["id"], "tr_ai_1")

        # 4. Platform filter for Bluesky / LinkedIn (professional tech focus)
        res_bsky = self.client.get("/api/trends?platform=bluesky")
        self.assertEqual(res_bsky.status_code, 200)
        data_bsky = res_bsky.json()
        self.assertEqual(data_bsky["count"], 2)  # ai_tech and frontier_paper
        for t in data_bsky["trends"]:
            self.assertIn(t["category"], ["ai_tech", "frontier_paper", "explainer"])

        # 5. Limit filter
        res_limit = self.client.get("/api/trends?limit=1")
        self.assertEqual(res_limit.status_code, 200)
        self.assertEqual(res_limit.json()["count"], 1)

    def test_get_trends_schema_completeness(self):
        self._seed_sample_trends()
        res = self.client.get("/api/trends")
        self.assertEqual(res.status_code, 200)
        trend = res.json()["trends"][0]

        expected_fields = [
            "id", "title", "summary", "source", "category",
            "url", "score", "discovered_at", "published_at",
            "is_sensitive", "metadata"
        ]
        for field in expected_fields:
            self.assertIn(field, trend, f"Missing field in API response: {field}")

    @patch("feedparser.parse")
    @patch("requests.get")
    def test_post_trends_refresh_sync(self, mock_requests_get, mock_feedparser):
        # Mock external calls to avoid live network requests
        mock_feedparser.side_effect = Exception("Mocked feed error")
        mock_requests_get.side_effect = Exception("Mocked HTTP error")

        payload = {"geo": "IN", "background": False, "limit": 5}
        res = self.client.post("/api/trends/refresh", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("trends", data)
        # NeuBench curated fallback stories will still succeed
        self.assertGreaterEqual(data["total_refreshed"], 1)

    def test_post_trends_refresh_background(self):
        payload = {"geo": "IN", "background": True}
        res = self.client.post("/api/trends/refresh", json=payload)
        self.assertEqual(res.status_code, 202)
        data = res.json()
        self.assertEqual(data["status"], "accepted")
        self.assertTrue(data["background"])

    def test_error_handling_corrupted_cache(self):
        # Write corrupted JSON to cache file
        self.temp_cache_file.write_text("{ corrupt json invalid !!!", encoding="utf-8")
        
        # Endpoint must handle corruption recovery gracefully without raising 500
        res = self.client.get("/api/trends")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 0)

    @patch("src.web.app.get_live_bluesky_metrics")
    def test_existing_dashboard_endpoints_still_work(self, mock_bsky):
        mock_bsky.return_value = {"followers": 16, "following": 8, "posts": 20, "timestamp": 123456}

        # 1. Topics API
        res_topics = self.client.get("/api/topics")
        self.assertEqual(res_topics.status_code, 200)
        self.assertIn("available_topics", res_topics.json())

        # 2. Stats API
        res_stats = self.client.get("/api/stats")
        self.assertEqual(res_stats.status_code, 200)
        data_stats = res_stats.json()
        self.assertIn("profile", data_stats)
        self.assertIn("platforms", data_stats)

        # 3. Auth Status API
        res_auth = self.client.get("/api/auth/status")
        self.assertEqual(res_auth.status_code, 200)
        self.assertIn("x", res_auth.json())


if __name__ == "__main__":
    unittest.main()
