import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.scheduler import AutomaterEngine
from src.tracker import ActivityTracker


class XTrendIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.metrics_file = Path(self.temp_dir.name) / "trial_metrics.json"
        self.history_file = Path(self.temp_dir.name) / "post_history.json"
        
        # Initialize empty tracker files
        self.tracker = ActivityTracker(self.metrics_file, self.history_file)
        
        # Engine with dry-run safety
        self.engine = AutomaterEngine()
        self.engine.history_file = self.history_file
        self.engine.tracker = self.tracker
        self.engine.safety.dry_run = True

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_new_ranked_trends_selected_and_context_reaches_ai(self):
        candidate_trends = [
            {
                "id": "tr_1",
                "title": "Quantum Error Correction Threshold Achieved",
                "summary": "Breakthrough demonstration of logical qubit fidelity.",
                "source": "TechCrunch",
                "category": "ai_tech",
                "url": "https://bench.example.com/quantum",
                "score": 18.5,
                "is_sensitive": False,
                "metadata": {"sources_seen": ["TechCrunch"]}
            }
        ]

        with patch.object(self.engine.hunter, "get_x_growth_topics", return_value=[]), \
             patch.object(self.engine.hunter, "get_candidate_trends", return_value=candidate_trends), \
             patch.object(self.engine.ai, "generate_hot_take", return_value="Quantum physics just roasted my morning coffee.") as mock_generate, \
             patch.object(self.engine.twitter, "post_tweet", return_value=True):

            success = self.engine._execute_original_post(time.time())
            self.assertTrue(success)

            # Verify generate_hot_take called with title and enriched context
            mock_generate.assert_called_once()
            called_title, called_context = mock_generate.call_args[0]
            self.assertEqual(called_title, "Quantum Error Correction Threshold Achieved")
            self.assertIn("Breakthrough demonstration", called_context)
            self.assertIn("Source: TechCrunch", called_context)
            self.assertIn("Category: ai_tech", called_context)
            # Outbound URLs are intentionally excluded from generation context.
            self.assertNotIn("URL:", called_context)

    def test_empty_cache_falls_back_to_legacy_topics(self):
        on_niche = [
            {
                "title": "Why context windows are not free",
                "summary": "Long context costs memory and latency.",
                "category": "ai_tech",
                "source": "Builder Notes",
                "url": "",
            }
        ]

        with patch.object(self.engine.hunter, "get_x_growth_topics", return_value=on_niche), \
             patch.object(self.engine.hunter, "get_candidate_trends", return_value=[]), \
             patch.object(self.engine.ai, "generate_hot_take", return_value="Context is not free.") as mock_generate, \
             patch.object(self.engine.twitter, "post_tweet", return_value=True):

            success = self.engine._execute_original_post(time.time())
            self.assertTrue(success)

            mock_generate.assert_called_once()
            called_title, _ = mock_generate.call_args[0]
            self.assertEqual(called_title, "Why context windows are not free")

    def test_trend_source_failure_falls_back_safely(self):
        on_niche = [
            {
                "title": "Cheap models vs frontier models",
                "summary": "Most production features do not need the largest model.",
                "category": "ai_tech",
                "source": "Builder Notes",
                "url": "",
            }
        ]

        # Simulate exception in get_candidate_trends
        with patch.object(self.engine.hunter, "get_x_growth_topics", return_value=on_niche), \
             patch.object(self.engine.hunter, "get_candidate_trends", side_effect=RuntimeError("Trend cache unavailable")), \
             patch.object(self.engine.ai, "generate_hot_take", return_value="Routing beats scale here.") as mock_generate, \
             patch.object(self.engine.twitter, "post_tweet", return_value=True):

            success = self.engine._execute_original_post(time.time())
            self.assertTrue(success)

            mock_generate.assert_called_once()
            called_title, _ = mock_generate.call_args[0]
            self.assertEqual(called_title, "Cheap models vs frontier models")

    def test_sensitive_content_retains_safeguards_and_is_skipped(self):
        candidate_trends = [
            {
                "id": "tr_sens_1",
                "title": "Violent Clash Breaks Out During Communal Procession",
                "summary": "Heated controversy and curfew imposed.",
                "source": "Google Trends (IN)",
                "category": "breaking_news",
                "url": "https://example.com/sensitive",
                "score": 25.0,  # Highly ranked!
                "is_sensitive": True,  # Sensitive!
                "metadata": {"sources_seen": ["Google Trends (IN)"]}
            },
            {
                "id": "tr_safe_2",
                "title": "ISRO Tests Cryogenic Upper Stage for Chandrayaan-4",
                "summary": "Successful hot test completed at Mahendragiri propulsion complex.",
                "source": "Google Trends (IN)",
                "category": "breaking_news",
                "url": "https://example.com/isro",
                "score": 15.0,
                "is_sensitive": False,
                "metadata": {"sources_seen": ["Google Trends (IN)"]}
            }
        ]

        with patch.object(self.engine.hunter, "get_x_growth_topics", return_value=[]), \
             patch.object(self.engine.hunter, "get_candidate_trends", return_value=candidate_trends), \
             patch.object(self.engine.ai, "generate_hot_take", return_value="Rocket science roast.") as mock_generate, \
             patch.object(self.engine.twitter, "post_tweet", return_value=True):

            success = self.engine._execute_original_post(time.time())
            self.assertTrue(success)

            # Ensure the sensitive trend was SKIPPED despite having a higher score (25.0 vs 15.0)
            mock_generate.assert_called_once()
            called_title, _ = mock_generate.call_args[0]
            self.assertEqual(called_title, "ISRO Tests Cryogenic Upper Stage for Chandrayaan-4")

    def test_all_candidates_and_legacy_sensitive_aborts_without_publishing(self):
        # All candidate trends are sensitive
        candidate_trends = [
            {
                "id": "tr_sens_1",
                "title": "Violent Clash Breaks Out During Communal Procession",
                "summary": "Heated controversy.",
                "source": "Google Trends (IN)",
                "category": "breaking_news",
                "score": 25.0,
                "is_sensitive": True,
                "metadata": {}
            }
        ]
        # All legacy fallback topics are sensitive
        legacy_sensitive = [
            {"title": "Hindu-Muslim riot inquiry commission report tabled", "context": "Communal tensions in town."}
        ]

        with patch.object(self.engine.hunter, "get_x_growth_topics", return_value=[]), \
             patch.object(self.engine.hunter, "get_candidate_trends", return_value=candidate_trends), \
             patch.object(self.engine.hunter, "get_x_unfiltered_topics", return_value=legacy_sensitive), \
             patch.object(self.engine.hunter, "get_casual_topics", return_value=[]), \
             patch.object(self.engine.ai, "generate_hot_take") as mock_generate, \
             patch.object(self.engine.twitter, "post_tweet") as mock_post:

            success = self.engine._execute_original_post(time.time())
            # Must return False and never call AI generation or twitter post
            self.assertFalse(success)
            mock_generate.assert_not_called()
            mock_post.assert_not_called()

            # Verify skipped event recorded
            events = self.tracker.metrics.get("recent_events", [])
            self.assertEqual(events[-1]["status"], "skipped")
            self.assertIn("sensitive", events[-1]["reason"].lower())


if __name__ == "__main__":
    unittest.main()
