"""Print aggregate project stats (for README updates)."""

from __future__ import annotations

import argparse
import json
import logging

from app.core.database import SessionLocal
from app.services.stats.project_stats_service import ProjectStatsService

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Print project aggregate stats as JSON")
    parser.add_argument(
        "--recent-runs",
        type=int,
        default=10,
        help="Number of recent completed runs to average (default: 10)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        stats = ProjectStatsService(db, recent_run_limit=args.recent_runs).get_stats()
        payload = {
            **stats.__dict__,
            "estimated_monthly_llm_cost_usd": round(stats.avg_estimated_llm_cost_usd * 30, 2),
        }
        print(json.dumps(payload, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
