import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.timezone_util import now as app_now
from app.models.alert import Alerts
from app.models.tracked_assets import TrackedAssets
from app.services.alerts.discord_notifier import send_discord_alert_if_configured
from app.services.sentiment.sentiment_service import SentimentService

logger = logging.getLogger(__name__)


class AlertService:
    """Alerts driven by rolling sentiment (article-weighted) and volume spikes vs prior-day baseline."""

    def __init__(self, db: Session):
        self.db = db
        self.sentiment_service = SentimentService(db)

    def rolling_window_bounds(self, end_date: datetime, window_days: int) -> Tuple[datetime, datetime]:
        end = self.sentiment_service.normalize_date_to_midnight(end_date)
        start = end - timedelta(days=window_days - 1)
        return start, end

    def article_weighted_rolling_sentiment(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> Optional[float]:
        rows = self.sentiment_service.get_sentiment_for_ticker_by_date_range(
            symbol, start_date, end_date
        )
        if not rows:
            return None

        weighted = 0.0
        total_articles = 0
        for row in rows:
            weighted += row.avg_sentiment * row.article_count
            total_articles += row.article_count

        if total_articles == 0:
            return None
        return weighted / total_articles

    def rolling_sentiment_below_threshold(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        threshold: Optional[float] = None,
    ) -> bool:
        limit = settings.NEGATIVE_SENTIMENT_THRESHOLD if threshold is None else threshold
        rolling = self.article_weighted_rolling_sentiment(symbol, start_date, end_date)
        if rolling is None:
            return False
        return rolling < limit

    def rolling_sentiment_above_threshold(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        threshold: Optional[float] = None,
    ) -> bool:
        limit = settings.POSITIVE_SENTIMENT_THRESHOLD if threshold is None else threshold
        rolling = self.article_weighted_rolling_sentiment(symbol, start_date, end_date)
        if rolling is None:
            return False
        return rolling > limit

    def volume_spike_ratio_latest_vs_prior(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        multiplier: Optional[float] = None,
    ) -> Optional[float]:
        mult = settings.VOLUME_SPIKE_MULTIPLIER if multiplier is None else multiplier
        rows = self.sentiment_service.get_sentiment_for_ticker_by_date_range(
            symbol, start_date, end_date
        )
        if len(rows) < 2:
            return None

        ordered = sorted(rows, key=lambda r: r.date)
        prior = ordered[:-1]
        latest = ordered[-1]
        baseline = sum(r.article_count for r in prior) / len(prior)
        today_count = latest.article_count

        if baseline == 0:
            return float(today_count) if today_count > 0 else None

        ratio = today_count / baseline
        if today_count >= mult * baseline:
            return ratio
        return None

    def create_alert(
        self,
        ticker_id: UUID,
        trigger_reason: str,
        sentiment_value: float,
    ) -> Alerts:
        alert = Alerts(
            ticker_id=ticker_id,
            trigger_reason=trigger_reason,
            sentiment_value=sentiment_value,
            created_at=app_now(),
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        send_discord_alert_if_configured(alert, db=self.db)
        return alert

    def get_alerts_for_ticker(self, ticker_id: UUID) -> List[Alerts]:
        return self.db.query(Alerts).filter(Alerts.ticker_id == ticker_id).all()

    def get_recent_alerts(self, limit: int = 50) -> List[Alerts]:
        return (
            self.db.query(Alerts)
            .order_by(Alerts.created_at.desc())
            .limit(limit)
            .all()
        )

    def _recent_alert_exists(self, ticker_id: UUID, trigger_reason: str) -> bool:
        cutoff = app_now() - timedelta(hours=settings.ALERT_COOLDOWN_HOURS)
        return (
            self.db.query(Alerts)
            .filter(
                Alerts.ticker_id == ticker_id,
                Alerts.trigger_reason == trigger_reason,
                Alerts.created_at >= cutoff,
            )
            .first()
            is not None
        )

    def evaluate_tracked_asset(self, asset: TrackedAssets, as_of: datetime) -> int:
        """Check thresholds for one symbol; returns number of alerts created."""
        symbol = asset.symbol
        ticker_id = asset.ticker_id
        start, end = self.rolling_window_bounds(as_of, settings.ROLLING_WINDOW_DAYS)
        created = 0

        rolling = self.article_weighted_rolling_sentiment(symbol, start, end)
        if rolling is not None and rolling < settings.NEGATIVE_SENTIMENT_THRESHOLD:
            reason = "negative_rolling_sentiment"
            if not self._recent_alert_exists(ticker_id, reason):
                self.create_alert(
                    ticker_id,
                    f"{symbol} rolling sentiment {rolling:.3f} below {settings.NEGATIVE_SENTIMENT_THRESHOLD}",
                    rolling,
                )
                created += 1

        if rolling is not None and rolling > settings.POSITIVE_SENTIMENT_THRESHOLD:
            reason = "positive_rolling_sentiment"
            if not self._recent_alert_exists(ticker_id, reason):
                self.create_alert(
                    ticker_id,
                    f"{symbol} rolling sentiment {rolling:.3f} above {settings.POSITIVE_SENTIMENT_THRESHOLD}",
                    rolling,
                )
                created += 1

        spike = self.volume_spike_ratio_latest_vs_prior(symbol, start, end)
        if spike is not None:
            reason = "volume_spike"
            if not self._recent_alert_exists(ticker_id, reason):
                self.create_alert(
                    ticker_id,
                    f"{symbol} article volume spike ({spike:.1f}x baseline)",
                    rolling if rolling is not None else 0.0,
                )
                created += 1

        return created

    def evaluate_all_tracked(self, assets: List[TrackedAssets], as_of: datetime) -> int:
        return sum(self.evaluate_tracked_asset(asset, as_of) for asset in assets)
