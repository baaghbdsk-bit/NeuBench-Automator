"""Tests for the growth publishing helpers."""

import unittest

from src.growth import (
    filter_fresh_topics,
    is_near_duplicate_topic,
    sanitize_plan,
    sanitize_publish_text,
    topic_similarity,
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


if __name__ == "__main__":
    unittest.main()
