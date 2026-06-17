"""
Recompute sentiment_daily rollups from article_entities (by processed_at ET day).

Usage (from backend/):
    python -m scripts.reaggregate_sentiment
    python -m scripts.reaggregate_sentiment --days 7
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import timedelta

from app.core.database import SessionLocal
from app.core.timezone_util import now
from app.services.sentiment.sentiment_service import SentimentService
from app.services.tracked_assets.tracked_assets_service import TrackedAssetsService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute sentiment_daily rollups")
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of ET calendar days to recompute, counting back from today (default: 1)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        sentiment = SentimentService(db)
        assets = TrackedAssetsService(db).list_all()
        symbols = [a.symbol for a in assets]
        today = now().date()

        for offset in range(args.days):
            day = today - timedelta(days=offset)
            for symbol in symbols:
                row = sentiment.aggregate_sentiment_for_ticker(symbol, day)
                if row.article_count:
                    logger.info(
                        "%s %s: count=%s avg=%.3f",
                        symbol,
                        row.date,
                        row.article_count,
                        row.avg_sentiment,
                    )

        logger.info("Reaggregated %s symbol(s) over %s day(s)", len(symbols), args.days)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
