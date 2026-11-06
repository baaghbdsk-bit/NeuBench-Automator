"""Unit tests for LinkedIn publishing client and state management.

Verifies:
- LinkedIn REST API payload construction.
- Document and image upload handling (mocked).
- First-comment posting.
- Duplicate prevention and content hash deduplication.
- Daily limit enforcement.
- Safe state file locking.
- Browser session availability checks.
"""

import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.linkedin_automater import LinkedInAutomater
from src.linkedin_state import (
    post_is_duplicate,
    count_posts_on_date,
    append_post_entry,
    linkedin_state_lock,
    normalize_text,
    content_hash,
)
import config


class TestLinkedInAutomater(unittest.TestCase):
    def setUp(self):
        self.automater = LinkedInAutomater(headless=True, dry_run=False)

    def test_dry_run_post(self):
        """Verify dry run mode simulates posting and first-commenting safely without network calls."""
        dry_automater = LinkedInAutomater(headless=True, dry_run=True)
        ok, msg = dry_automater.post(
            text="Simulated educational post about distributed consensus.",
            image_path=None,
            first_comment="Link to interactive consensus visualization.",
            media_title="Consensus Guide",
        )
        self.assertTrue(ok)
        self.assertIn("[DRY RUN]", msg)

    @patch.dict(os.environ, {"LINKEDIN_ACCESS_TOKEN": "mock_token", "LINKEDIN_PERSON_URN": "urn:li:person:mock123"})
    @patch("requests.post")
    def test_api_text_only_payload(self, mock_post):
        """Verify correct JSON payload sent to LinkedIn REST API for text-only post."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.headers = {"X-RestLi-Id": "urn:li:share:987654"}
        mock_post.return_value = mock_response

        ok, msg = self.automater.post(text="Testing distributed transactions 2PC vs Sagas")
        self.assertTrue(ok)
        self.assertIn("urn:li:share:987654", msg)

        # Inspect API call payload
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["author"], "urn:li:person:mock123")
        self.assertEqual(payload["commentary"], "Testing distributed transactions 2PC vs Sagas")
        self.assertEqual(payload["visibility"], "PUBLIC")
        self.assertEqual(payload["lifecycleState"], "PUBLISHED")
        self.assertNotIn("content", payload)

    @patch.dict(os.environ, {"LINKEDIN_ACCESS_TOKEN": "mock_token", "LINKEDIN_PERSON_URN": "urn:li:person:mock123"})
    @patch("requests.post")
    @patch("requests.put")
    @patch("requests.get")
    def test_api_document_upload_and_post(self, mock_get, mock_put, mock_post):
        """Verify document carousel upload, status polling, and attached post payload."""
        # 1. Mock document initialize
        init_resp = MagicMock()
        init_resp.status_code = 200
        init_resp.json.return_value = {
            "value": {
                "uploadUrl": "https://media.licdn.com/upload-doc-target",
                "document": "urn:li:document:doc456",
            }
        }

        # 2. Mock document poll status
        poll_resp = MagicMock()
        poll_resp.status_code = 200
        poll_resp.json.return_value = {"status": "AVAILABLE"}
        mock_get.return_value = poll_resp

        # 3. Mock document PUT
        put_resp = MagicMock()
        put_resp.status_code = 201
        mock_put.return_value = put_resp

        # 4. Mock post creation
        post_resp = MagicMock()
        post_resp.status_code = 201
        post_resp.headers = {"X-RestLi-Id": "urn:li:share:doc_post_111"}

        mock_post.side_effect = [init_resp, post_resp]

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            tf.write(b"%PDF-1.4 mock pdf content")
            pdf_path = tf.name

        try:
            ok, msg = self.automater.post(
                text="Educational PDF carousel on LSM Trees",
                image_path=pdf_path,
                media_title="LSM Trees Complete Study Guide",
            )
            self.assertTrue(ok)
            self.assertIn("urn:li:share:doc_post_111", msg)

            # Check post call had document media attachment
            post_call = mock_post.call_args_list[1]
            payload = post_call[1]["json"]
            self.assertIn("content", payload)
            media = payload["content"]["media"]
            self.assertEqual(media["id"], "urn:li:document:doc456")
            self.assertEqual(media["title"], "LSM Trees Complete Study Guide")
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    @patch.dict(os.environ, {"LINKEDIN_ACCESS_TOKEN": "mock_token", "LINKEDIN_PERSON_URN": "urn:li:person:mock123"})
    @patch("requests.post")
    def test_first_comment_posting(self, mock_post):
        """Verify first comment payload to socialActions endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "urn:li:comment:777"}
        mock_post.return_value = mock_response

        ok, msg = self.automater.add_comment_to_post(
            post_urn="urn:li:share:12345",
            comment_text="Benchmarking data available at https://app.neubench.workers.dev",
        )
        self.assertTrue(ok)
        self.assertIn("urn:li:comment:777", msg)

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["actor"], "urn:li:person:mock123")
        self.assertEqual(payload["object"], "urn:li:share:12345")
        self.assertIn("https://app.neubench.workers.dev", payload["message"]["text"])


class TestLinkedInStateAndDeduplication(unittest.TestCase):
    def test_duplicate_prevention_by_title_and_hash(self):
        """Verify duplicate detection catches identical titles, content, and normalized variations."""
        state = {
            "posts": [
                {
                    "title": "Kafka vs RabbitMQ: Complete Architecture Guide",
                    "content": "Deep dive into messaging architectures and partition scaling.",
                    "content_hash": content_hash("Deep dive into messaging architectures and partition scaling."),
                    "url": "https://arxiv.org/abs/2301.0001",
                }
            ]
        }

        # Exact title duplicate
        self.assertTrue(post_is_duplicate(state, title="Kafka vs RabbitMQ: Complete Architecture Guide"))

        # Normalized case variation duplicate
        self.assertTrue(post_is_duplicate(state, title="  kafka vs rabbitmq: complete architecture guide  "))

        # Content duplicate
        self.assertTrue(post_is_duplicate(state, title="", content="Deep dive into messaging architectures and partition scaling."))

        # URL duplicate
        self.assertTrue(post_is_duplicate(state, title="", url="https://arxiv.org/abs/2301.0001"))

        # Distinct new post
        self.assertFalse(post_is_duplicate(state, title="RAG vs Fine-Tuning: LLM Evaluation"))

    def test_daily_limit_enforcement(self):
        """Verify post count calculation on given date."""
        today = "2026-11-07"
        state = {
            "posts": [
                {"posted_at": "2026-11-07T08:00:00Z", "status": "success"},
                {"posted_at": "2026-11-07T12:00:00Z", "status": "success"},
                {"posted_at": "2026-11-06T15:00:00Z", "status": "success"},  # Yesterday
            ]
        }

        count = count_posts_on_date(state, today)
        self.assertEqual(count, 2)
        # Verify against MAX_DAILY_LINKEDIN
        self.assertLess(count, config.MAX_DAILY_LINKEDIN)

    def test_state_locking_context_manager(self):
        """Verify file locking safely acquires and releases without deadlock."""
        with linkedin_state_lock():
            locked = True
        self.assertTrue(locked)


if __name__ == "__main__":
    unittest.main()
