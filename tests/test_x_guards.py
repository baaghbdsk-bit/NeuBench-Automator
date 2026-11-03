import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.tracker import ActivityTracker
from src.twitter_client import TwitterClient
from src.x_state import (
    complete_reservation,
    load_x_history,
    reserve_original,
    reserve_target,
)


class ErrorResponse:
    url = "https://x.com/i/api/graphql/CreateTweet"
    status = 200

    def json(self):
        return {"errors": [{"message": "rejected"}]}


class NoJsonResponse:
    url = "https://x.com/i/api/graphql/CreateTweet"
    status = 200

    def json(self):
        raise ValueError("body unavailable")


class XGuardTests(unittest.TestCase):
    def test_unknown_original_reservation_blocks_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            history_file = Path(directory) / "post_history.json"
            reservation, reason = reserve_original(
                history_file,
                target_identifier="Topic A",
                text="A durable X post",
            )
            self.assertIsNotNone(reservation, reason)

            complete_reservation(
                history_file,
                reservation,
                outcome="unknown",
                target_identifier="Topic A",
                reason="browser timeout after submission",
            )

            retry, retry_reason = reserve_original(
                history_file,
                target_identifier="Topic A",
                text="A durable X post",
            )
            self.assertIsNone(retry)
            self.assertIn("already", retry_reason.lower())
            self.assertEqual(load_x_history(history_file)["pending_x_actions"][0]["status"], "unknown")

    def test_successful_target_reservation_is_deduplicated(self):
        with tempfile.TemporaryDirectory() as directory:
            history_file = Path(directory) / "post_history.json"
            reservation, _ = reserve_target(
                history_file,
                action_type="reply",
                target_identifier="https://x.com/example/status/1",
                text="A useful reply",
            )
            self.assertIsNotNone(reservation)
            complete_reservation(
                history_file,
                reservation,
                outcome="success",
                target_identifier="https://x.com/example/status/1",
            )

            duplicate, _ = reserve_target(
                history_file,
                action_type="reply",
                target_identifier="https://x.com/example/status/1",
                text="A different reply",
            )
            self.assertIsNone(duplicate)
            self.assertIn(
                "https://x.com/example/status/1",
                load_x_history(history_file)["replied_urls"],
            )

    def test_tracker_history_alias_persists_new_x_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            metrics_file = Path(directory) / "metrics.json"
            history_file = Path(directory) / "post_history.json"
            tracker = ActivityTracker(metrics_file, history_file)
            tracker.history["posted_tweet_hashes"].append("hash")
            tracker.save_history()

            saved = json.loads(history_file.read_text(encoding="utf-8"))
            self.assertEqual(saved["posted_tweet_hashes"], ["hash"])
            self.assertIn("pending_x_actions", saved)

    def test_create_tweet_response_validation(self):
        client = TwitterClient(dry_run=True)
        success = SimpleNamespace(
            url="https://x.com/i/api/graphql/CreateTweet",
            status=200,
            json=lambda: {"data": {"create_tweet": {}}},
        )
        unrelated = SimpleNamespace(url="https://x.com/i/api/graphql/Home", status=200)

        self.assertTrue(client._response_confirms_tweet(success))
        self.assertFalse(client._response_confirms_tweet(ErrorResponse()))
        self.assertTrue(client._response_confirms_tweet(NoJsonResponse()))
        self.assertFalse(client._response_confirms_tweet(unrelated))

    def test_missing_confirmation_is_unknown_not_success(self):
        client = TwitterClient(dry_run=False)
        locator = MagicMock()
        locator.first = locator
        locator.get_attribute.return_value = "false"
        locator.is_disabled.return_value = False
        locator.all_inner_texts.return_value = []

        page = MagicMock()
        page.locator.return_value = locator
        page.pages = []
        page.new_page.return_value = page
        page.keyboard = MagicMock()

        context = MagicMock()
        context.pages = [page]
        browser = MagicMock()
        browser.new_context.return_value = context
        playwright = MagicMock()
        playwright.chromium.launch.return_value = browser
        playwright_context = MagicMock()
        playwright_context.__enter__.return_value = playwright
        playwright_context.__exit__.return_value = False

        client._human_type = lambda _element, _text: None
        with patch("src.twitter_client.sync_playwright", return_value=playwright_context), patch(
            "src.twitter_client.time.sleep", return_value=None
        ):
            ok = client.post_tweet("No confirmation smoke test")

        self.assertFalse(ok)
        self.assertTrue(client.last_outcome_unknown)


if __name__ == "__main__":
    unittest.main()
