from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.timezone_util import app_tz, calendar_day_bounds, start_of_local_day, to_local_date
from app.models.article import ArticleEntities, Articles
from app.models.sentiment import SentimentDaily
from app.models.tracked_assets import TrackedAssets


class SentimentService:
    def __init__(self, db: Session):
        self.db = db

    def _resolve_ticker_id(self, symbol: str) -> UUID:
        asset = (
            self.db.query(TrackedAssets)
            .filter(TrackedAssets.symbol == symbol.strip().upper())
            .first()
        )
        if not asset:
            raise LookupError(f"Tracked asset not found: {symbol}")
        return asset.ticker_id

    def _to_date(self, value: datetime | date) -> date:
        return to_local_date(value)

    def _day_bounds(self, value: datetime | date) -> Tuple[datetime, datetime]:
        """Application timezone calendar day [start, end) for daily rollups."""
        return calendar_day_bounds(value)

    def _entity_in_local_day(self, day_start: datetime, day_end: datetime):
        """
        Match entities analyzed on this ET calendar day (processed_at).

        Legacy rows with null processed_at fall back to article published_at.
        """
        return or_(
            and_(
                ArticleEntities.processed_at.isnot(None),
                ArticleEntities.processed_at >= day_start,
                ArticleEntities.processed_at < day_end,
            ),
            and_(
                ArticleEntities.processed_at.is_(None),
                Articles.published_at >= day_start,
                Articles.published_at < day_end,
            ),
        )

    def _entities_for_symbol_on_date(self, symbol: str, value: datetime | date) -> List[ArticleEntities]:
        day_start, day_end = self._day_bounds(value)
        return (
            self.db.query(ArticleEntities)
            .join(Articles, ArticleEntities.article_id == Articles.article_id)
            .join(TrackedAssets, ArticleEntities.ticker_id == TrackedAssets.ticker_id)
            .filter(TrackedAssets.symbol == symbol.strip().upper())
            .filter(self._entity_in_local_day(day_start, day_end))
            .all()
        )

    def _symbols_with_articles_on_date(self, value: datetime | date) -> List[str]:
        day_start, day_end = self._day_bounds(value)
        rows = (
            self.db.query(TrackedAssets.symbol)
            .join(ArticleEntities, ArticleEntities.ticker_id == TrackedAssets.ticker_id)
            .join(Articles, ArticleEntities.article_id == Articles.article_id)
            .filter(self._entity_in_local_day(day_start, day_end))
            .distinct()
            .all()
        )
        return [row[0] for row in rows]

    def get_last_analyzed_at_map(
        self, pairs: list[tuple[str, date]]
    ) -> dict[tuple[str, date], datetime | None]:
        """Latest ``processed_at`` per (symbol, analysis_date) for API responses."""
        wanted = set(pairs)
        result: dict[tuple[str, date], datetime | None] = {pair: None for pair in pairs}
        if not wanted:
            return result

        symbols = {symbol for symbol, _ in pairs}
        min_day = min(day for _, day in pairs)
        max_day = max(day for _, day in pairs)
        range_start, _ = calendar_day_bounds(min_day)
        _, range_end = calendar_day_bounds(max_day)

        rows = (
            self.db.query(TrackedAssets.symbol, ArticleEntities.processed_at)
            .join(TrackedAssets, ArticleEntities.ticker_id == TrackedAssets.ticker_id)
            .filter(TrackedAssets.symbol.in_(symbols))
            .filter(ArticleEntities.processed_at.isnot(None))
            .filter(ArticleEntities.processed_at >= range_start)
            .filter(ArticleEntities.processed_at < range_end)
            .all()
        )
        for symbol, processed_at in rows:
            key = (symbol, to_local_date(processed_at))
            if key not in wanted:
                continue
            current = result[key]
            if current is None or processed_at > current:
                result[key] = processed_at
        return result

    def create_sentiment_for_ticker(
        self,
        symbol: str,
        day: datetime | date,
        avg_sentiment: float,
        article_count: int,
        momentum: float,
        std_div: Optional[float] = None,
    ) -> SentimentDaily:
        ticker_id = self._resolve_ticker_id(symbol)
        day = self._to_date(day)
        existing = self.get_sentiment_for_ticker_by_date(symbol, day)
        if existing:
            return self.update_sentiment_for_ticker(
                symbol, day, avg_sentiment, article_count, momentum, std_div
            )
        row = SentimentDaily(
            ticker_id=ticker_id,
            date=day,
            avg_sentiment=avg_sentiment,
            article_count=article_count,
            momentum=momentum,
            std_div=std_div,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_sentiment_for_all_tickers(self) -> List[SentimentDaily]:
        return self.db.query(SentimentDaily).all()

    def get_sentiment_for_ticker_by_date(
        self, symbol: str, day: datetime | date
    ) -> Optional[SentimentDaily]:
        ticker_id = self._resolve_ticker_id(symbol)
        day = self._to_date(day)
        return (
            self.db.query(SentimentDaily)
            .filter(SentimentDaily.ticker_id == ticker_id, SentimentDaily.date == day)
            .first()
        )

    def get_sentiment_for_all_tickers_by_date(self, day: datetime | date) -> List[SentimentDaily]:
        day = self._to_date(day)
        return self.db.query(SentimentDaily).filter(SentimentDaily.date == day).all()

    def get_sentiment_for_ticker_by_date_range(
        self, symbol: str, start_date: datetime | date, end_date: datetime | date
    ) -> List[SentimentDaily]:
        ticker_id = self._resolve_ticker_id(symbol)
        start = self._to_date(start_date)
        end = self._to_date(end_date)
        return (
            self.db.query(SentimentDaily)
            .filter(
                SentimentDaily.ticker_id == ticker_id,
                SentimentDaily.date >= start,
                SentimentDaily.date <= end,
            )
            .all()
        )

    def get_sentiment_for_all_tickers_by_date_range(
        self, start_date: datetime | date, end_date: datetime | date
    ) -> List[SentimentDaily]:
        start = self._to_date(start_date)
        end = self._to_date(end_date)
        return (
            self.db.query(SentimentDaily)
            .filter(SentimentDaily.date >= start, SentimentDaily.date <= end)
            .all()
        )

    def get_sentiment_for_all_tickers_by_date_above_threshold(
        self, day: datetime | date, threshold: float
    ) -> List[SentimentDaily]:
        day = self._to_date(day)
        return (
            self.db.query(SentimentDaily)
            .filter(SentimentDaily.date == day, SentimentDaily.avg_sentiment > threshold)
            .all()
        )

    def get_sentiment_for_all_tickers_by_date_below_threshold(
        self, day: datetime | date, threshold: float
    ) -> List[SentimentDaily]:
        day = self._to_date(day)
        return (
            self.db.query(SentimentDaily)
            .filter(SentimentDaily.date == day, SentimentDaily.avg_sentiment < threshold)
            .all()
        )

    def update_sentiment_for_ticker(
        self,
        symbol: str,
        day: datetime | date,
        avg_sentiment: float,
        article_count: int,
        momentum: float,
        std_div: Optional[float] = None,
    ) -> SentimentDaily:
        existing = self.get_sentiment_for_ticker_by_date(symbol, day)
        if not existing:
            raise LookupError("Sentiment not found for ticker")
        existing.avg_sentiment = avg_sentiment
        existing.article_count = article_count
        existing.momentum = momentum
        existing.std_div = std_div
        self.db.commit()
        self.db.refresh(existing)
        return existing

    def delete_sentiment_for_ticker(self, symbol: str, day: datetime | date) -> None:
        existing = self.get_sentiment_for_ticker_by_date(symbol, day)
        if not existing:
            return
        self.db.delete(existing)
        self.db.commit()

    def normalize_date_to_midnight(self, value: datetime) -> datetime:
        """Kept for alert service window helpers."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=app_tz())
        return start_of_local_day(value)

    def aggregate_sentiment_for_ticker(self, symbol: str, day: datetime | date) -> SentimentDaily:
        day_date = self._to_date(day)
        entities_today = self._entities_for_symbol_on_date(symbol, day_date)
        if not entities_today:
            previous = self.get_sentiment_for_ticker_by_date(
                symbol, day_date - timedelta(days=1)
            )
            momentum = (0.0 - previous.avg_sentiment) if previous else 0.0
            return self.create_sentiment_for_ticker(symbol, day_date, 0.0, 0, momentum)

        scores = [e.sentiment_score for e in entities_today if e.sentiment_score is not None]
        article_count = len(entities_today)
        avg_sentiment = sum(scores) / len(scores) if scores else 0.0
        std_div = None
        if len(scores) > 1:
            mean = avg_sentiment
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
            std_div = variance**0.5

        previous = self.get_sentiment_for_ticker_by_date(symbol, day_date - timedelta(days=1))
        if not previous:
            previous = self.create_sentiment_for_ticker(symbol, day_date - timedelta(days=1), 0.0, 0, 0.0)

        momentum = avg_sentiment - previous.avg_sentiment
        return self.create_sentiment_for_ticker(
            symbol, day_date, avg_sentiment, article_count, momentum, std_div
        )

    def aggregate_sentiment_for_all_tickers(self, day: datetime | date) -> List[SentimentDaily]:
        symbols = self._symbols_with_articles_on_date(day)
        if not symbols:
            return []
        return [self.aggregate_sentiment_for_ticker(s, day) for s in symbols]
