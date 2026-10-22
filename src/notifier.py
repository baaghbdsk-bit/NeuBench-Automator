import os
import requests
from typing import Optional
import config

class PushNotifier:
    """Dispatches real-time alerts to Discord or Telegram when cycles execute."""

    def __init__(self):
        self.discord_url = getattr(config, "DISCORD_WEBHOOK_URL", os.getenv("DISCORD_WEBHOOK_URL", "")).strip()
        self.telegram_token = getattr(config, "TELEGRAM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN", "")).strip()
        self.telegram_chat_id = getattr(config, "TELEGRAM_CHAT_ID", os.getenv("TELEGRAM_CHAT_ID", "")).strip()

    def send_action_alert(
        self,
        action_type: str,
        content_preview: str,
        target_account_or_url: str = "",
        status: str = "success",
        is_dry_run: bool = False
    ):
        """Sends an alert if either Discord or Telegram credentials are provided."""
        if not self.discord_url and not (self.telegram_token and self.telegram_chat_id):
            return

        dry_prefix = "[DRY-RUN] " if is_dry_run else ""
        action_title = f"{dry_prefix}NeuBench-Automator: {action_type.replace('_', ' ').title()} ({status.upper()})"

        # 1. Dispatch to Discord
        if self.discord_url:
            self._send_discord(action_title, action_type, content_preview, target_account_or_url, status, is_dry_run)

        # 2. Dispatch to Telegram
        if self.telegram_token and self.telegram_chat_id:
            self._send_telegram(action_title, action_type, content_preview, target_account_or_url, status)

    def _send_discord(self, title, action_type, text, target, status, is_dry):
        color = 0x00ba7c if status == "success" else 0xf59e0b if status == "skipped" else 0xef4444
        embed = {
            "title": title,
            "description": f"**Content:**\n> {text}\n\n**Target:** {target or 'NeuBench AI Radar'}",
            "color": color,
            "footer": {
                "text": "NeuBench-Automator 24/7 Engine • 𝕏 + Bluesky + Omnichannel"
            }
        }
        try:
            requests.post(self.discord_url, json={"embeds": [embed]}, timeout=4)
        except Exception as e:
            print(f"[Notifier] Discord alert failed: {e}")

    def _send_telegram(self, title, action_type, text, target, status):
        msg = f"⚡ *{title}*\n\n📝 *Take:* {text}\n🎯 *Target:* {target or 'NeuBench AI Radar'}"
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        try:
            requests.post(url, json={"chat_id": self.telegram_chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=4)
        except Exception as e:
            print(f"[Notifier] Telegram alert failed: {e}")

