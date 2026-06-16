from unittest.mock import Mock, patch
from uuid import uuid4

from app.models.alert import Alerts
from app.services.alerts.discord_notifier import send_discord_alert_if_configured


def _alert() -> Alerts:
    return Alerts(
        alert_id=uuid4(),
        ticker_id=uuid4(),
        trigger_reason="test",
        sentiment_value=-0.5,
    )


class TestDiscordNotifier:
    def test_skips_when_url_missing(self):
        with patch("app.services.alerts.discord_notifier.settings") as mock_settings:
            mock_settings.DISCORD_WEBHOOK_URL = None
            with patch("app.services.alerts.discord_notifier.httpx.post") as post:
                send_discord_alert_if_configured(_alert())
                post.assert_not_called()

    def test_skips_dummy_placeholder_url(self):
        with patch("app.services.alerts.discord_notifier.settings") as mock_settings:
            mock_settings.DISCORD_WEBHOOK_URL = "dummy val"
            with patch("app.services.alerts.discord_notifier.httpx.post") as post:
                send_discord_alert_if_configured(_alert())
                post.assert_not_called()

    def test_posts_when_url_is_valid(self):
        with patch("app.services.alerts.discord_notifier.settings") as mock_settings:
            mock_settings.DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/123/token"
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            with patch("app.services.alerts.discord_notifier.httpx.post", return_value=mock_response) as post:
                send_discord_alert_if_configured(_alert())
                post.assert_called_once()
