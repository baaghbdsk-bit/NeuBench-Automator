import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.indian_influence_engine import (
    IndianInfluenceDatabase,
    OpportunityQueueManager,
    IndianEngagementEngine,
)


class IndianInfluenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "indian_accounts.json"
        self.queue_path = Path(self.temp_dir.name) / "engagement_queue.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_database_initialization_and_categories(self):
        db = IndianInfluenceDatabase(self.db_path)
        accounts = db.get_accounts_by_category()
        self.assertGreaterEqual(len(accounts), 25)

        categories = set(a.get("category") for a in accounts)
        self.assertIn("Politics & Governance", categories)
        self.assertIn("News & Journalism", categories)
        self.assertIn("Society & Culture", categories)
        self.assertIn("Business & Technology", categories)
        self.assertIn("Entertainment & Sports", categories)

    def test_priority_targets_filtering(self):
        db = IndianInfluenceDatabase(self.db_path)
        tier1 = db.get_priority_monitoring_targets(tier=1, limit=5)
        self.assertLessEqual(len(tier1), 5)
        for acc in tier1:
            self.assertEqual(acc.get("priority_tier"), 1)

    def test_queue_enqueuing_and_deduplication(self):
        qm = OpportunityQueueManager(self.queue_path)
        opp = qm.enqueue_opportunity(
            tweet_url="https://x.com/AshwiniVaishnaw/status/123",
            author="AshwiniVaishnaw",
            tweet_text="India semiconductor mission achieves new milestone in fab construction.",
            category="Business & Technology",
            suggested_reply="A critical supply chain foundation for domestic electronics.",
            why_relevant="Key infrastructure discussion",
            is_sensitive=False
        )
        self.assertEqual(opp.get("status"), "approved")

        # Duplicate must return empty and not be enqueued twice
        duplicate = qm.enqueue_opportunity(
            tweet_url="https://x.com/AshwiniVaishnaw/status/123",
            author="AshwiniVaishnaw",
            tweet_text="Duplicate test",
            category="Business & Technology",
            suggested_reply="Duplicate reply",
            why_relevant="Duplicate",
            is_sensitive=False
        )
        self.assertEqual(duplicate, {})

    def test_sensitive_political_gating(self):
        qm = OpportunityQueueManager(self.queue_path)
        opp = qm.enqueue_opportunity(
            tweet_url="https://x.com/politician/status/456",
            author="politician",
            tweet_text="Major controversy over waqf board amendments and communal tensions.",
            category="Politics & Governance",
            suggested_reply="Balanced observation on legal frameworks.",
            why_relevant="Sensitive debate",
            is_sensitive=True
        )
        # Sensitive debate must be gated behind pending_approval
        self.assertEqual(opp.get("status"), "pending_approval")
        pending = qm.get_pending_approvals()
        self.assertEqual(len(pending), 1)

        # Approve opportunity
        qm.approve_opportunity(opp["id"])
        self.assertEqual(len(qm.get_pending_approvals()), 0)
        self.assertEqual(len(qm.get_ready_to_publish(limit=5)), 1)

    def test_sensitivity_detection_heuristics(self):
        mock_twitter = MagicMock()
        mock_ai = MagicMock()
        mock_tracker = MagicMock()
        engine = IndianEngagementEngine(mock_twitter, mock_ai, mock_tracker)

        is_sens, _ = engine.detect_sensitivity(
            "Heated debate on communal tensions and waqf properties across the state.",
            "Politics & Governance"
        )
        self.assertTrue(is_sens)

        is_sens_clean, _ = engine.detect_sensitivity(
            "UPI transactions touched an all-time monthly high of 16 billion.",
            "Business & Technology"
        )
        self.assertFalse(is_sens_clean)


if __name__ == "__main__":
    unittest.main()
