import logging
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import Alerts

logger = logging.getLogger(__name__)


def _is_valid_webhook_url(url: str) -> bool:
    cleaned = url.strip()
    return cleaned.startswith("https://") or cleaned.startswith("http://")


def send_discord_alert_if_configured(alert: Alerts, db: Optional[Session] = None) -> None:
    """
    POST a message to the configured Discord webhook. No-op if URL is unset or invalid.
    Failures are logged; they do not affect alert persistence.
    """
    url: Optional[str] = settings.DISCORD_WEBHOOK_URL
    if not url or not _is_valid_webhook_url(str(url)):
        logger.debug("Discord webhook not configured; skipping notification")
        return

    symbol = "unknown"
    if alert.tracked_asset is not None:
        symbol = alert.tracked_asset.symbol
    elif db is not None:
        db.refresh(alert, attribute_names=["tracked_asset"])
        if alert.tracked_asset:
            symbol = alert.tracked_asset.symbol

    payload = {
        "content": (
            f"Alert for **{symbol}**: {alert.trigger_reason} "
            f"(sentiment={alert.sentiment_value:.4f}, id={alert.alert_id})"
        )
    }

    try:
        response = httpx.post(str(url).strip(), json=payload, timeout=15.0)
        response.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("Discord webhook request failed: %s", e)
    except Exception as e:
        logger.warning("Discord notification error: %s", e)
