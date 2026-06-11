import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Set

from dateutil import parser as date_parser
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.article import ArticleEntities, Articles
from app.models.processing_runs import ProcessingRuns
from app.models.tracked_assets import TrackedAssets
from app.services.alerts.alert_service import AlertService
from app.services.filtering.keyword_filter import build_search_text, match_tracked_assets
from app.services.ingestion.article_ingestion_service import ArticleIngestionService
from app.services.llm.ai_service import LLMService
from app.services.sentiment.sentiment_service import SentimentService
from app.services.tracked_assets.tracked_assets_service import TrackedAssetsService

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    run_id: str
    status: str
    articles_fetched: int = 0
    articles_keyword_matched: int = 0
    articles_processed: int = 0
    articles_skipped: int = 0
    alerts_created: int = 0
    symbols_aggregated: List[str] = field(default_factory=list)
    error: str | None = None


class PipelineService:
    """Fetch → keyword filter → LLM → store → rollup → alerts."""

    def __init__(self, db: Session):
        self.db = db
        self.ingestion = ArticleIngestionService()
        self.llm = LLMService()
        self.sentiment = SentimentService(db)
        self.alerts = AlertService(db)
        self.assets = TrackedAssetsService(db)

    def run(self) -> PipelineResult:
        run = ProcessingRuns(
            articles_fetched=0,
            num_processed=0,
            status="running",
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        try:
            return self._execute(run)
        except Exception as exc:
            logger.exception("Pipeline failed")
            run.status = "error"
            run.finished_at = datetime.now(timezone.utc)
            run.raw_text = traceback.format_exc()[-4000:]
            self.db.commit()
            return PipelineResult(
                run_id=str(run.run_id),
                status="error",
                articles_fetched=run.articles_fetched,
                articles_processed=run.num_processed,
                error=str(exc),
            )

    def _execute(self, run: ProcessingRuns) -> PipelineResult:
        tracked = self.assets.list_all()
        if not tracked:
            logger.warning("No tracked assets, add symbols before running the pipeline")
            run.status = "completed"
            run.finished_at = datetime.now(timezone.utc)
            run.raw_text = "No tracked assets configured"
            self.db.commit()
            return PipelineResult(run_id=str(run.run_id), status="completed")

        now = datetime.now(timezone.utc)
        from_date = (now - timedelta(hours=settings.HOURS_BACK)).strftime("%Y-%m-%d")
        to_date = now.strftime("%Y-%m-%d")

        fetched = self.ingestion.fetch_articles(
            query=settings.NEWS_QUERY,
            from_date=from_date,
            to_date=to_date,
            max_pages=settings.NEWS_MAX_PAGES,
        )
        run.articles_fetched = len(fetched)

        new_articles = self.ingestion.filter_new_articles(fetched)
        keyword_matched = 0
        processed = 0
        skipped = 0
        symbols_touched: Set[str] = set()
        aggregation_dates: Dict[str, Set[datetime]] = {}

        for raw in new_articles:
            matches = match_tracked_assets(build_search_text(raw), tracked)
            if not matches:
                skipped += 1
                continue

            keyword_matched += 1
            body = self._article_body(raw)
            title = raw["title"]

            summary = self.llm.summarize_article(title, body)
            sentiment = self.llm.classify_sentiment(title, body)
            published_at = self._parse_published_at(raw.get("publishedAt"))
            source_name = self._source_name(raw)

            article = Articles(
                title=title,
                source=source_name,
                url=raw["url"],
                published_at=published_at,
                summary=summary,
                raw_text=body or None,
            )
            self.db.add(article)
            self.db.flush()

            processed_at = datetime.now(timezone.utc)
            for match in matches:
                entity = ArticleEntities(
                    article_id=article.article_id,
                    ticker_id=match.ticker_id,
                    confidence=match.confidence,
                    sentiment_score=sentiment.sentiment_score,
                    relevance_score=match.confidence,
                    processed_at=processed_at,
                )
                self.db.add(entity)
                symbols_touched.add(match.symbol)
                aggregation_dates.setdefault(match.symbol, set()).add(published_at)

            self.db.commit()
            processed += 1
            logger.info("Processed: %s (%s)", title[:80], ", ".join(m.symbol for m in matches))

        symbols_aggregated: List[str] = []
        for symbol in sorted(symbols_touched):
            for published_at in aggregation_dates.get(symbol, {now}):
                self.sentiment.aggregate_sentiment_for_ticker(symbol, published_at)
            symbols_aggregated.append(symbol)

        alerts_created = self.alerts.evaluate_all_tracked(tracked, now)

        run.num_processed = processed
        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        run.raw_text = (
            f"keyword_matched={keyword_matched}, skipped={skipped}, "
            f"alerts={alerts_created}, symbols={','.join(symbols_aggregated) or 'none'}"
        )
        self.db.commit()

        return PipelineResult(
            run_id=str(run.run_id),
            status="completed",
            articles_fetched=run.articles_fetched,
            articles_keyword_matched=keyword_matched,
            articles_processed=processed,
            articles_skipped=skipped,
            alerts_created=alerts_created,
            symbols_aggregated=symbols_aggregated,
        )

    @staticmethod
    def _article_body(article: dict) -> str:
        return (article.get("content") or article.get("description") or "").strip()

    @staticmethod
    def _source_name(article: dict) -> str:
        source = article.get("source") or {}
        if isinstance(source, dict):
            return source.get("name") or "unknown"
        return str(source)

    @staticmethod
    def _parse_published_at(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        parsed = date_parser.isoparse(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
