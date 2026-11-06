"""Unit tests for LinkedIn AI generation, content format classification, and plan validation.

Verifies:
- Content format selector (comparison_carousel vs handwritten_notes vs professional_carousel).
- Plan schema and educational depth validation (validate_educational_plan).
- Deduplication against history.
- Fallback plan generation logic.
"""

import unittest
from unittest.mock import patch

from src.ai_generator import (
    AIGenerator,
    select_linkedin_content_format,
    validate_educational_plan,
)
from src.linkedin_state import post_is_duplicate


class TestLinkedInAI(unittest.TestCase):
    def setUp(self):
        self.ai = AIGenerator()

    def test_select_linkedin_content_format_comparison(self):
        """Verify comparison/versus topics are classified into comparison_carousel."""
        fmt1 = select_linkedin_content_format("Kafka vs RabbitMQ", "Comparing event streaming vs message queues")
        self.assertEqual(fmt1, "comparison_carousel")

        fmt2 = select_linkedin_content_format("REST versus GraphQL", "API architecture design choices")
        self.assertEqual(fmt2, "comparison_carousel")

        fmt3 = select_linkedin_content_format("RAG or Fine-Tuning", "LLM specialization trade-offs")
        self.assertEqual(fmt3, "comparison_carousel")

    def test_select_linkedin_content_format_handwritten_notes(self):
        """Verify deep architecture, protocols, and data structures are classified into handwritten_notes."""
        fmt1 = select_linkedin_content_format("PostgreSQL B-Tree Index Internals", "Deep dive into page layout and node splits")
        self.assertEqual(fmt1, "handwritten_notes")

        fmt2 = select_linkedin_content_format("TCP 3-Way Handshake Protocol", "How SYN, SYN-ACK, and ACK establish connections")
        self.assertEqual(fmt2, "handwritten_notes")

        fmt3 = select_linkedin_content_format("Raft Distributed Consensus Algorithm", "Leader election, log replication, and split brain prevention")
        self.assertEqual(fmt3, "handwritten_notes")

    def test_select_linkedin_content_format_professional_carousel(self):
        """Verify breaking industry events and benchmark releases route to professional_carousel."""
        fmt1 = select_linkedin_content_format("Cloudflare Massive Network Outage", "Analysis of route leaks and root cause")
        self.assertEqual(fmt1, "professional_carousel")

        fmt2 = select_linkedin_content_format("Llama 3 Released", "Benchmarking inference speed and quantization accuracy")
        self.assertEqual(fmt2, "professional_carousel")

    def test_validate_educational_plan_rejects_shallow(self):
        """Verify validate_educational_plan rejects invalid, truncated, or shallow plans."""
        # Non-dict
        valid, msg = validate_educational_plan("invalid")
        self.assertFalse(valid)

        # Missing post text
        valid, msg = validate_educational_plan({"post_text": ""})
        self.assertFalse(valid)

        # Post text too short
        valid, msg = validate_educational_plan({"post_text": "Too short"})
        self.assertFalse(valid)
        self.assertIn("too short", msg.lower())

        # Too few pages (post text valid > 80 chars)
        shallow_plan = {
            "post_text": "Here is an in-depth post about operating systems and memory pagination across distributed virtual memory nodes.",
            "pages": [
                {"type": "cover", "title": "OS Paging"},
                {"type": "concept", "title": "Paging", "body": "Paging is virtual memory."},
            ],
        }
        valid, msg = validate_educational_plan(shallow_plan)
        self.assertFalse(valid)
        self.assertIn("minimum 4 required", msg)

        # Concept page with < 80 chars body
        shallow_concept = {
            "post_text": "Here is an in-depth post about operating systems and memory pagination across distributed virtual memory nodes.",
            "pages": [
                {"type": "cover", "title": "OS Paging"},
                {"type": "concept", "title": "Paging", "body": "Too short body."},
                {"type": "diagram", "title": "Paging Diagram"},
                {"type": "cta", "title": "Summary"},
            ],
        }
        valid, msg = validate_educational_plan(shallow_concept)
        self.assertFalse(valid)
        self.assertIn("too short", msg.lower())

    def test_validate_educational_plan_accepts_dense(self):
        """Verify validate_educational_plan accepts dense multi-page educational plans."""
        dense_plan = {
            "post_text": "Understanding how Raft consensus protocol achieves replicated state machines across distributed nodes in production systems without split brain.",
            "pages": [
                {"type": "cover", "title": "Raft Consensus Protocol"},
                {
                    "type": "concept",
                    "title": "Leader Election",
                    "body": "When heartbeat timer expires, a follower increments term, transitions to candidate, and requests votes from all peer nodes across the cluster.",
                },
                {"type": "diagram", "title": "Term Replication Flow"},
                {"type": "cta", "title": "Golden Rules"},
            ],
        }
        valid, msg = validate_educational_plan(dense_plan)
        self.assertTrue(valid)

    def test_deduplication_against_history(self):
        """Verify candidate topics are matched against historical posts."""
        state = {
            "posts": [
                {"title": "Hash Table Collisions: Chaining vs Open Addressing", "posted_at": "2026-11-06T10:00:00Z", "status": "success"},
                {"title": "Zero-Copy Networking: sendfile vs splice", "posted_at": "2026-11-05T10:00:00Z", "status": "success"},
            ]
        }
        self.assertTrue(post_is_duplicate(state, title="Hash Table Collisions: Chaining vs Open Addressing"))
        self.assertTrue(post_is_duplicate(state, title="  hash table collisions: chaining vs open addressing  "))
        self.assertFalse(post_is_duplicate(state, title="Consistent Hashing in DynamoDB"))

    def test_comparison_plan_fallback_structure(self):
        """Verify generate_comparison_plan returns a valid 6-page plan structure even under mock fallback."""
        with patch.object(self.ai, "_generate_with_fallback", side_effect=Exception("API limit")):
            plan = self.ai.generate_comparison_plan("Kafka vs RabbitMQ", "Message streaming vs queuing")
            self.assertIn("pages", plan)
            self.assertGreaterEqual(len(plan["pages"]), 4)
            self.assertIn("Kafka", plan.get("post_text", ""))
            self.assertIn("RabbitMQ", plan.get("post_text", ""))

    def test_educational_notes_plan_fallback_structure(self):
        """Verify generate_educational_notes_plan returns a valid 6-page plan structure under fallback."""
        with patch.object(self.ai, "_generate_with_fallback", side_effect=Exception("API limit")):
            plan = self.ai.generate_educational_notes_plan("LSM-Tree Storage Engine", "Log-Structured Merge Trees")
            self.assertIn("pages", plan)
            self.assertGreaterEqual(len(plan["pages"]), 4)
            self.assertIn("LSM-Tree", plan.get("post_text", ""))


if __name__ == "__main__":
    unittest.main()
