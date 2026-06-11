from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

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
        if isinstance(value, datetime):
            return value.date()
        return value

    def _day_bounds(self, value: datetime | date) -> Tuple[datetime, datetime]:
        """UTC calendar day [start, end) for filtering article published_at."""
        d = self._to_date(value)
        start = datetime.combine(d, datetime.min.time())
        return start, start + timedelta(days=1)

    def _entities_for_symbol_on_date(self, symbol: str, value: datetime | date) -> List[ArticleEntities]:
        day_start, day_end = self._day_bounds(value)
        return (
            self.db.query(ArticleEntities)
            .join(Articles, ArticleEntities.article_id == Articles.article_id)
            .join(TrackedAssets, ArticleEntities.ticker_id == TrackedAssets.ticker_id)
            .filter(TrackedAssets.symbol == symbol.strip().upper())
            .filter(Articles.published_at >= day_start)
            .filter(Articles.published_at < day_end)
            .all()
        )

    def _symbols_with_articles_on_date(self, value: datetime | date) -> List[str]:
        day_start, day_end = self._day_bounds(value)
        rows = (
            self.db.query(TrackedAssets.symbol)
            .join(ArticleEntities, ArticleEntities.ticker_id == TrackedAssets.ticker_id)
            .join(Articles, ArticleEntities.article_id == Articles.article_id)
            .filter(Articles.published_at >= day_start)
            .filter(Articles.published_at < day_end)
            .distinct()
            .all()
        )
        return [row[0] for row in rows]

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
        return value.replace(hour=0, minute=0, second=0, microsecond=0)

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
