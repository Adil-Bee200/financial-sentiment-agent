"""
Seed tracked_assets for the news pipeline.

Usage (from backend/):
    python -m scripts.seed_assets
    python -m scripts.seed_assets --list
    python -m scripts.seed_assets --file path/to/assets.json
    python -m scripts.seed_assets --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from app.core.database import SessionLocal
from app.seeds.loader import DEFAULT_SEED_FILE, load_seed_file, seed_tracked_assets
from app.services.tracked_assets.tracked_assets_service import TrackedAssetsService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed tracked_assets for the pipeline")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_SEED_FILE,
        help=f"JSON seed file (default: {DEFAULT_SEED_FILE.name})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without writing to the database",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List tracked assets currently in the database",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    db = SessionLocal()
    try:
        if args.list:
            assets = TrackedAssetsService(db).list_all()
            if not assets:
                logger.info("No tracked assets in database")
                return 0
            for asset in assets:
                parts = [asset.symbol]
                if asset.company_name:
                    parts.append(asset.company_name)
                if asset.sector:
                    parts.append(f"({asset.sector})")
                logger.info("  %s", " — ".join(parts))
            logger.info("Total: %s", len(assets))
            return 0

        seed_assets = load_seed_file(args.file)
        result = seed_tracked_assets(db, seed_assets, dry_run=args.dry_run)

        if result.created:
            action = "Would create" if args.dry_run else "Created"
            logger.info("%s: %s", action, ", ".join(result.created))
        if result.skipped:
            logger.info("Skipped (already exist): %s", ", ".join(result.skipped))
        for error in result.errors:
            logger.error("%s", error)

        if result.errors:
            return 1
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
