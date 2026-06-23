import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Set

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.timezone_util import now as app_now, parse_external_datetime
from app.models.article import ArticleEntities, Articles
from app.models.processing_runs import ProcessingRuns
from app.services.alerts.alert_service import AlertService
from app.services.filtering.article_scorer import rank_articles_for_llm
from app.services.ingestion.article_ingestion_service import ArticleIngestionService
from app.services.pipeline.llm_content import (
    build_llm_input,
    count_llm_articles_today,
    remaining_llm_budget_for_run,
)
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
    articles_skipped_no_keyword: int = 0
    articles_skipped_llm_limit: int = 0
    llm_budget_remaining_start: int = 0
    alerts_created: int = 0
    symbols_aggregated: List[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class MatchedArticlePreview:
    title: str
    url: str
    published_at: str
    source: str
    symbols: List[str]
    would_send_to_llm: bool
    priority_score: float = 0.0


@dataclass
class PipelinePreviewResult:
    status: str
    tracked_symbol_count: int = 0
    articles_fetched: int = 0
    articles_new: int = 0
    articles_keyword_matched: int = 0
    articles_skipped_no_keyword: int = 0
    articles_would_llm: int = 0
    articles_over_llm_budget: int = 0
    llm_budget_remaining: int = 0
    matched_articles: List[MatchedArticlePreview] = field(default_factory=list)
    rejected_articles: List[MatchedArticlePreview] = field(default_factory=list)
    error: str | None = None


class PipelineService:
    """Fetch → dedupe → keyword filter → LLM (capped) → store → rollup → alerts."""

    def __init__(self, db: Session):
        self.db = db
        self.ingestion = ArticleIngestionService()
        self._llm = None
        self._sentiment = None
        self._alerts = None
        self.assets = TrackedAssetsService(db)

    @property
    def llm(self):
        if self._llm is None:
            from app.services.llm.ai_service import LLMService

            self._llm = LLMService()
        return self._llm

    @property
    def sentiment(self):
        if self._sentiment is None:
            self._sentiment = SentimentService(self.db)
        return self._sentiment

    @property
    def alerts(self):
        if self._alerts is None:
            self._alerts = AlertService(self.db)
        return self._alerts

    def preview(self, *, include_rejected: bool = False) -> PipelinePreviewResult:
        """
        Dry run: fetch news, dedupe, keyword filter — stop before LLM or DB writes.
        No OpenAI key required.
        """
        try:
            tracked = self.assets.list_all()
            if not tracked:
                logger.warning("No tracked assets — add symbols before previewing the pipeline")
                return PipelinePreviewResult(status="completed", tracked_symbol_count=0)

            now = app_now()
            llm_budget = remaining_llm_budget_for_run(self.db, now)
            fetched, new_articles = self._fetch_new_articles(now, [asset.symbol for asset in tracked])

            matched_articles: List[MatchedArticlePreview] = []
            rejected_articles: List[MatchedArticlePreview] = []
            keyword_matched = 0
            skipped_no_keyword = 0
            would_llm = 0
            over_budget = 0

            ranked_candidates, skipped_no_keyword = rank_articles_for_llm(new_articles, tracked)
            keyword_matched = len(ranked_candidates)

            if include_rejected:
                matched_urls = {candidate.raw.get("url") for candidate in ranked_candidates}
                for raw in new_articles:
                    if raw.get("url") in matched_urls:
                        continue
                    rejected_articles.append(
                        MatchedArticlePreview(
                            title=(raw.get("title") or "").strip(),
                            url=raw.get("url") or "",
                            published_at=raw.get("publishedAt") or "",
                            source=self._source_name(raw),
                            symbols=[],
                            would_send_to_llm=False,
                        )
                    )

            for candidate in ranked_candidates:
                raw = candidate.raw
                matches = candidate.matches
                send_to_llm = would_llm < llm_budget
                if send_to_llm:
                    would_llm += 1
                else:
                    over_budget += 1

                matched_articles.append(
                    MatchedArticlePreview(
                        title=(raw.get("title") or "").strip(),
                        url=raw.get("url") or "",
                        published_at=raw.get("publishedAt") or "",
                        source=self._source_name(raw),
                        symbols=[m.symbol for m in matches],
                        would_send_to_llm=send_to_llm,
                        priority_score=candidate.priority_score,
                    )
                )

            return PipelinePreviewResult(
                status="completed",
                tracked_symbol_count=len(tracked),
                articles_fetched=len(fetched),
                articles_new=len(new_articles),
                articles_keyword_matched=keyword_matched,
                articles_skipped_no_keyword=skipped_no_keyword,
                articles_would_llm=would_llm,
                articles_over_llm_budget=over_budget,
                llm_budget_remaining=llm_budget,
                matched_articles=matched_articles,
                rejected_articles=rejected_articles,
            )
        except Exception as exc:
            logger.exception("Pipeline preview failed")
            return PipelinePreviewResult(status="error", error=str(exc))

    def run(self) -> PipelineResult:
        run = ProcessingRuns(
            articles_fetched=0,
            num_processed=0,
            status="running",
            started_at=app_now(),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        try:
            return self._execute(run)
        except Exception as exc:
            logger.exception("Pipeline failed")
            run.status = "error"
            run.finished_at = app_now()
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
            logger.warning("No tracked assets — add symbols before running the pipeline")
            run.status = "completed"
            run.finished_at = app_now()
            run.raw_text = "No tracked assets configured"
            self.db.commit()
            return PipelineResult(run_id=str(run.run_id), status="completed")

        now = app_now()
        llm_budget = remaining_llm_budget_for_run(self.db, now)
        already_today = count_llm_articles_today(self.db, now)
        logger.info(
            "LLM budget: %s/%s used today, %s slots this run (daily cap %s, per-run cap %s)",
            already_today,
            settings.MAX_LLM_ARTICLES_PER_DAY,
            llm_budget,
            settings.MAX_LLM_ARTICLES_PER_DAY,
            settings.MAX_LLM_ARTICLES_PER_RUN or "off",
        )

        fetched, new_articles = self._fetch_new_articles(now, [asset.symbol for asset in tracked])
        run.articles_fetched = len(fetched)
        keyword_matched = 0
        processed = 0
        skipped_no_keyword = 0
        skipped_llm_limit = 0
        llm_used_this_run = 0
        llm_prompt_tokens = 0
        llm_completion_tokens = 0
        estimated_llm_cost_usd = 0.0
        symbols_touched: Set[str] = set()
        aggregation_dates: Dict[str, Set[datetime]] = {}

        ranked_candidates, skipped_no_keyword = rank_articles_for_llm(new_articles, tracked)
        keyword_matched = len(ranked_candidates)

        for candidate in ranked_candidates:
            raw = candidate.raw
            matches = candidate.matches

            if llm_used_this_run >= llm_budget:
                skipped_llm_limit += 1
                continue

            title, llm_content = build_llm_input(raw)
            analysis = self.llm.analyze_article(title, llm_content)
            if not analysis.ok:
                logger.warning(
                    "LLM failed for %s (%s): %s",
                    title[:80],
                    analysis.error_kind,
                    analysis.error_message,
                )
                continue

            summary = analysis.summary
            sentiment = analysis.sentiment
            if summary is None or sentiment is None:
                logger.warning("LLM returned ok=True without summary/sentiment for %s", title[:80])
                continue

            llm_prompt_tokens += analysis.usage.prompt_tokens
            llm_completion_tokens += analysis.usage.completion_tokens
            estimated_llm_cost_usd += analysis.usage.estimated_cost_usd
            published_at = self._parse_published_at(raw.get("publishedAt"))
            source_name = self._source_name(raw)
            stored_body = self._article_body_for_storage(raw)

            article = Articles(
                title=title,
                source=source_name,
                url=raw["url"],
                published_at=published_at,
                summary=summary,
                raw_text=stored_body or None,
            )
            self.db.add(article)
            self.db.flush()

            processed_at = app_now()
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
                aggregation_dates.setdefault(match.symbol, set()).add(processed_at)

            self.db.commit()
            processed += 1
            llm_used_this_run += 1
            logger.info(
                "LLM processed (priority=%.2f): %s (%s)",
                candidate.priority_score,
                title[:80],
                ", ".join(m.symbol for m in matches),
            )

        symbols_aggregated: List[str] = []
        for symbol in sorted(symbols_touched):
            days = aggregation_dates.get(symbol, set())
            days.add(now)
            for day in days:
                self.sentiment.aggregate_sentiment_for_ticker(symbol, day)
            symbols_aggregated.append(symbol)

        alerts_created = self.alerts.evaluate_all_tracked(tracked, now)

        run.num_processed = processed
        run.articles_keyword_matched = keyword_matched
        run.articles_skipped_llm_limit = skipped_llm_limit
        run.alerts_created = alerts_created
        run.llm_prompt_tokens = llm_prompt_tokens
        run.llm_completion_tokens = llm_completion_tokens
        run.estimated_llm_cost_usd = round(estimated_llm_cost_usd, 4)
        run.status = "completed"
        run.finished_at = app_now()
        run.raw_text = (
            f"keyword_matched={keyword_matched}, no_keyword={skipped_no_keyword}, "
            f"llm_limit_skipped={skipped_llm_limit}, llm_used_run={llm_used_this_run}, "
            f"alerts={alerts_created}, symbols={','.join(symbols_aggregated) or 'none'}"
        )
        self.db.commit()

        return PipelineResult(
            run_id=str(run.run_id),
            status="completed",
            articles_fetched=run.articles_fetched,
            articles_keyword_matched=keyword_matched,
            articles_processed=processed,
            articles_skipped_no_keyword=skipped_no_keyword,
            articles_skipped_llm_limit=skipped_llm_limit,
            llm_budget_remaining_start=llm_budget,
            alerts_created=alerts_created,
            symbols_aggregated=symbols_aggregated,
        )

    def _fetch_new_articles(self, now: datetime, tracked_symbols: List[str] | None = None) -> tuple[List[dict], List[dict]]:
        from_date, to_date = self.ingestion.build_date_range(settings.HOURS_BACK, now)
        supplement_symbols = tracked_symbols if settings.NEWS_SUPPLEMENT_TICKER_FETCH else None

        fetched = self.ingestion.fetch_for_pipeline(
            query=settings.NEWS_QUERY,
            from_date=from_date,
            to_date=to_date,
            max_pages=settings.NEWS_MAX_PAGES,
            supplement_symbols=supplement_symbols,
        )
        new_articles = self._sort_by_published_desc(self.ingestion.filter_new_articles(fetched))
        return fetched, new_articles

    @staticmethod
    def _sort_by_published_desc(articles: List[dict]) -> List[dict]:
        """Newest first so the daily LLM cap favors recent articles."""

        def sort_key(article: dict) -> str:
            return article.get("publishedAt") or ""

        return sorted(articles, key=sort_key, reverse=True)

    @staticmethod
    def _article_body_for_storage(article: dict) -> str:
        return (article.get("content") or article.get("description") or "").strip()

    @staticmethod
    def _source_name(article: dict) -> str:
        source = article.get("source") or {}
        if isinstance(source, dict):
            return source.get("name") or "unknown"
        return str(source)

    @staticmethod
    def _parse_published_at(value: str | None) -> datetime:
        return parse_external_datetime(value)
