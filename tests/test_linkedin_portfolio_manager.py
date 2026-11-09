# -*- coding: utf-8 -*-
"""
Unit tests for LinkedInPortfolioManager
"""

import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile
from src.linkedin_portfolio_manager import LinkedInPortfolioManager, GENERIC_COMPONENT_BLOCKLIST


class TestLinkedInPortfolioManager(unittest.TestCase):

    def setUp(self):
        self.mgr = LinkedInPortfolioManager(ai_generator=None)

    def test_decide_portfolio_format_flow_gif(self):
        topic = "AllReduce Ring Topology: Real-time Gradient Dispatch Flow"
        fmt, reason = self.mgr.decide_portfolio_format(topic)
        self.assertEqual(fmt, "animated_flow_gif")
        self.assertIn("looping flow diagram", reason)

    def test_decide_portfolio_format_notebook_carousel(self):
        topic = "B-Tree Internals and Page Splitting: Engineering Study Notes"
        fmt, reason = self.mgr.decide_portfolio_format(topic)
        self.assertEqual(fmt, "notebook_carousel")
        self.assertIn("study guide", reason)

    def test_decide_portfolio_format_text_only(self):
        topic = "The Fallacy of Premature Microservices: Lessons from 10 Years in Production"
        fmt, reason = self.mgr.decide_portfolio_format(topic)
        self.assertEqual(fmt, "text_only")
        self.assertIn("authoritative", reason.lower())

    def test_explicit_format_override(self):
        topic = "AllReduce Ring Topology: Real-time Gradient Dispatch Flow"
        fmt, reason = self.mgr.decide_portfolio_format(topic, explicit_format="text_only")
        self.assertEqual(fmt, "text_only")

    def test_validate_article_quality_too_short(self):
        short_text = "Here is a brief post about databases. They are fast."
        ok, reason = self.mgr.validate_article_quality(short_text)
        self.assertFalse(ok)
        self.assertIn("below executive minimum", reason)

    def test_validate_article_quality_placeholder_rejected(self):
        text = "This is a detailed analysis of {topic} with comprehensive performance metrics. " * 30
        ok, reason = self.mgr.validate_article_quality(text)
        self.assertFalse(ok)
        self.assertIn("placeholder", reason.lower())

    def test_validate_article_quality_text_only_mismatch_rejected(self):
        text = ("Database indexing internals require deep analysis of write amplification. "
                "See the animated diagram below for the routing pipeline. " + ("Further technical metrics and analysis. " * 30))
        ok, reason = self.mgr.validate_article_quality(text, visual_format="text_only")
        self.assertFalse(ok)
        self.assertIn("references an attached visual", reason)

    def test_validate_visual_integrity_suppresses_generic_gif(self):
        with NamedTemporaryFile(suffix=".gif", delete=False) as f:
            f.write(b"GIF89a" + b"\x00" * 20000)
            gif_path = f.name

        try:
            generic_spec = {
                "components": [
                    {"name": "Client Ingest", "type": "input"},
                    {"name": "Parser & Schema", "type": "worker"},
                    {"name": "Cache Layer", "type": "cache"},
                    {"name": "Storage Sink", "type": "sink"},
                ]
            }
            ok, sanitized, reason = self.mgr.validate_visual_integrity(
                gif_path,
                visual_format="animated_flow_gif",
                topic="OnePlus ColorOS OTA Architecture",
                spec=generic_spec
            )
            self.assertFalse(ok)
            self.assertIsNone(sanitized)
            self.assertIn("generic components", reason.lower())
        finally:
            Path(gif_path).unlink(missing_ok=True)

    def test_validate_visual_integrity_accepts_clean_visual(self):
        with NamedTemporaryFile(suffix=".gif", delete=False) as f:
            f.write(b"GIF89a" + b"\x00" * 20000)
            gif_path = f.name

        try:
            topic_spec = {
                "components": [
                    {"name": "OTA Manifest Endpoint", "type": "input"},
                    {"name": "Device Tier Tagger", "type": "worker"},
                    {"name": "CDN Edge Throttle", "type": "router"},
                    {"name": "A/B Partition Switcher", "type": "sink"},
                ]
            }
            ok, sanitized, reason = self.mgr.validate_visual_integrity(
                gif_path,
                visual_format="animated_flow_gif",
                topic="OnePlus ColorOS OTA Architecture",
                spec=topic_spec
            )
            self.assertTrue(ok)
            self.assertEqual(sanitized, str(gif_path))
        finally:
            Path(gif_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
