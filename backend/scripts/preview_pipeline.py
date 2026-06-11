"""
Preview the pipeline through keyword filtering — no LLM calls or DB writes.

Usage (from backend/):
    python -m scripts.preview_pipeline
    python -m scripts.preview_pipeline --json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from app.core.database import SessionLocal
from app.services.pipeline.pipeline_service import PipelinePreviewResult, PipelineService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dry-run fetch + keyword filter (stops before LLM)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full preview result as JSON",
    )
    parser.add_argument(
        "--only-llm",
        action="store_true",
        help="List only articles that would be sent to the LLM this run",
    )
    return parser


def _preview_to_dict(result: PipelinePreviewResult) -> dict:
    return {
        "status": result.status,
        "error": result.error,
        "tracked_symbol_count": result.tracked_symbol_count,
        "articles_fetched": result.articles_fetched,
        "articles_new": result.articles_new,
        "articles_keyword_matched": result.articles_keyword_matched,
        "articles_skipped_no_keyword": result.articles_skipped_no_keyword,
        "articles_would_llm": result.articles_would_llm,
        "articles_over_llm_budget": result.articles_over_llm_budget,
        "llm_budget_remaining": result.llm_budget_remaining,
        "matched_articles": [
            {
                "title": article.title,
                "url": article.url,
                "published_at": article.published_at,
                "source": article.source,
                "symbols": article.symbols,
                "would_send_to_llm": article.would_send_to_llm,
            }
            for article in result.matched_articles
        ],
    }


def _print_human(result: PipelinePreviewResult, *, only_llm: bool) -> None:
    if result.error:
        logger.error("Preview failed: %s", result.error)
        return

    logger.info(
        "Preview summary: tracked=%s fetched=%s new=%s matched=%s "
        "no_keyword=%s would_llm=%s over_budget=%s llm_slots=%s",
        result.tracked_symbol_count,
        result.articles_fetched,
        result.articles_new,
        result.articles_keyword_matched,
        result.articles_skipped_no_keyword,
        result.articles_would_llm,
        result.articles_over_llm_budget,
        result.llm_budget_remaining,
    )

    articles = result.matched_articles
    if only_llm:
        articles = [a for a in articles if a.would_send_to_llm]

    if not articles:
        logger.info("No matching articles to show.")
        return

    logger.info("Matched articles (%s):", len(articles))
    for index, article in enumerate(articles, start=1):
        llm_tag = "LLM" if article.would_send_to_llm else "over budget"
        symbols = ", ".join(article.symbols)
        logger.info(
            "%s. [%s] (%s) %s — %s — %s",
            index,
            symbols,
            llm_tag,
            article.title,
            article.source,
            article.published_at,
        )


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    db = SessionLocal()
    try:
        result = PipelineService(db).preview()
        if args.json:
            print(json.dumps(_preview_to_dict(result), indent=2))
        else:
            _print_human(result, only_llm=args.only_llm)

        if result.status == "error":
            return 1
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
