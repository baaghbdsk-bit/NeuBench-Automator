import unittest

from src.instagram_automater import InstagramAutomater


class _FakeBody:
    def __init__(self, text):
        self.text = text

    def inner_text(self, timeout=0):
        return self.text


class _FakeDialogs:
    def __init__(self, visible):
        self.visible = visible

    def count(self):
        return 1 if self.visible else 0

    def nth(self, index):
        return self

    def is_visible(self):
        return self.visible


class _FakePage:
    def __init__(self, body_text="", dialog_visible=False):
        self.body_text = body_text
        self.dialog_visible = dialog_visible

    def locator(self, selector):
        if selector == "body":
            return _FakeBody(self.body_text)
        return _FakeDialogs(self.dialog_visible)

    def wait_for_timeout(self, milliseconds):
        pass


class InstagramConfirmationTests(unittest.TestCase):
    def test_confirmation_phrase_returns_true(self):
        page = _FakePage(body_text="Your reel has been shared.")
        self.assertTrue(InstagramAutomater()._await_share_confirmation(page, 1000))

    def test_closed_composer_returns_true(self):
        page = _FakePage(body_text="", dialog_visible=False)
        self.assertTrue(InstagramAutomater()._await_share_confirmation(page, 1000))

    def test_open_composer_without_confirmation_times_out(self):
        page = _FakePage(body_text="", dialog_visible=True)
        self.assertFalse(InstagramAutomater()._await_share_confirmation(page, 0))


if __name__ == "__main__":
    unittest.main()
