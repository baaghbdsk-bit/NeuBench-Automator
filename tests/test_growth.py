"""Tests for the growth publishing helpers."""

import unittest

from src.growth import (
    evidence_gate,
    extract_numeric_claims,
    filter_fresh_topics,
    first_comment_gate,
    is_near_duplicate_topic,
    sanitize_plan,
    sanitize_publish_text,
    topic_similarity,
    validate_no_number_without_source,
)


class SanitizePublishTextTests(unittest.TestCase):
    def test_removes_brand_name(self):
        self.assertEqual(
            sanitize_publish_text("NeuBench telemetry reveals a 40% gap."),
            "Telemetry reveals a 40% gap.",
        )

    def test_removes_urls(self):
        text = sanitize_publish_text("Full breakdown: https://example.com/post")
        self.assertNotIn("http", text)
        self.assertNotIn("example.com", text)

    def test_removes_brand_domain(self):
        text = sanitize_publish_text("Compare live: https://app.neubench.workers.dev")
        self.assertEqual(text, "")

    def test_keeps_clean_text_untouched(self):
        text = "Most RAG failures are retrieval failures, not generation failures."
        self.assertEqual(sanitize_publish_text(text), text)

    def test_capitalizes_repaired_line(self):
        text = sanitize_publish_text("Benchmarks: https://example.com/bench")
        self.assertEqual(text, "")

    def test_keeps_benchmark_heading(self):
        text = sanitize_publish_text("BENCHMARK: what to measure")
        self.assertEqual(text, "BENCHMARK: what to measure")

    def test_sanitizes_nested_plan(self):
        plan = {
            "cover": {"headline": "NeuBench latency notes"},
            "slides": [{"subhead": "Live on https://app.neubench.workers.dev"}],
        }
        cleaned = sanitize_plan(plan)
        self.assertEqual(cleaned["cover"]["headline"], "Latency notes")
        self.assertNotIn("neubench", str(cleaned).lower())


class TopicSimilarityTests(unittest.TestCase):
    def test_near_duplicate_titles_detected(self):
        self.assertTrue(
            is_near_duplicate_topic(
                "io_uring vs epoll in production",
                ["io_uring vs epoll: what changes in production"],
            )
        )

    def test_different_titles_are_fresh(self):
        self.assertFalse(
            is_near_duplicate_topic(
                "Vector database indexing trade-offs",
                ["Kubernetes autoscaling lessons from an outage"],
            )
        )

    def test_similarity_is_symmetric(self):
        left = "Frontier reasoning drift and cost per token"
        right = "Frontier reasoning cost per token drift"
        self.assertAlmostEqual(topic_similarity(left, right), topic_similarity(right, left))

    def test_filter_fresh_topics_drops_repeats(self):
        topics = [
            {"title": "io_uring vs epoll in production"},
            {"title": "Why context windows are not free"},
            {"title": "io_uring vs epoll: what changes in production"},
        ]
        fresh = filter_fresh_topics(topics, ["io_uring vs epoll in production"], limit=3)
        self.assertEqual([t["title"] for t in fresh], ["Why context windows are not free"])


class EvidenceGateTests(unittest.TestCase):
    def test_sourced_number_passes(self):
        ok, _, issues = evidence_gate(
            "I cut p99 latency on this path. The source says 60 percent was wasted.\n\nWhat do you measure first?",
            source_context="Measured 60 percent waste on this path",
        )
        self.assertTrue(ok, issues)

    def test_unsourced_number_is_rejected(self):
        ok, _, issues = evidence_gate(
            "Your cluster wastes 60 percent of its memory on empty air. Fix it here?",
            source_context="",
        )
        self.assertFalse(ok)
        self.assertTrue(any("unsourced number" in i for i in issues))

    def test_banned_opener_is_rejected(self):
        ok, _, issues = evidence_gate(
            "What is a Bloom Filter? Here is how it works. Why does it matter?",
            source_context="Bloom filters trade accuracy for memory",
        )
        self.assertFalse(ok)
        self.assertTrue(any("banned opener" in i for i in issues))

    def test_broken_template_is_rejected(self):
        ok, _, issues = evidence_gate(
            "Understanding the real-world mechanics of KV cache is one of the most critical fundamentals. Why does it matter?",
            source_context="KV cache stores attention keys",
        )
        self.assertFalse(ok)

    def test_repeated_title_is_rejected(self):
        title = "What is a Bloom Filter?"
        ok, _, issues = evidence_gate(
            f"{title}\n\nI stopped trusting {title} after a false positive. What would you test first?",
            topic_title=title,
            source_context="",
        )
        self.assertFalse(ok)
        self.assertTrue(any("repeated" in i for i in issues))

    def test_absolute_claim_is_rejected(self):
        ok, _, issues = evidence_gate(
            "I switched to this approach. The result is guaranteed zero failures. What do you use?",
            source_context="",
        )
        self.assertFalse(ok)

    def test_first_comment_requires_value_without_question(self):
        ok, _, issues = first_comment_gate(
            "One detail the post skips: the cache grows with sequence length even when traffic is flat."
        )
        self.assertTrue(ok, issues)
        ok, _, issues = first_comment_gate("What would you test first here?")
        self.assertFalse(ok)
        self.assertTrue(any("question" in i for i in issues))

    def test_extract_numeric_claims_normalises_units(self):
        ok_a, _ = validate_no_number_without_source("It costs 5 microseconds.", "measured 5µs here")
        ok_b, _ = validate_no_number_without_source("It costs 5 microseconds.", "")
        self.assertTrue(ok_a)
        self.assertFalse(ok_b)


if __name__ == "__main__":
    unittest.main()
