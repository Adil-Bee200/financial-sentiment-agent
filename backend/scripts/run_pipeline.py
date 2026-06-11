"""
Entrypoint for the cron pipeline (local or GitHub Actions).

Usage (from backend/):
    python -m scripts.run_pipeline
"""

import logging
import sys

from app.core.database import SessionLocal
from app.services.pipeline.pipeline_service import PipelineService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    db = SessionLocal()
    try:
        result = PipelineService(db).run()
        logger.info(
            "Pipeline %s: fetched=%s matched=%s processed=%s no_keyword=%s llm_limit=%s "
            "llm_budget_start=%s alerts=%s symbols=%s",
            result.status,
            result.articles_fetched,
            result.articles_keyword_matched,
            result.articles_processed,
            result.articles_skipped_no_keyword,
            result.articles_skipped_llm_limit,
            result.llm_budget_remaining_start,
            result.alerts_created,
            result.symbols_aggregated,
        )
        if result.error:
            logger.error("Error: %s", result.error)
        return 1 if result.status == "error" else 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
