from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from sqlalchemy.orm import Session

from app.services.tracked_assets.tracked_assets_service import TrackedAssetsService

DEFAULT_SEED_FILE = Path(__file__).with_name("tracked_assets_default.json")


@dataclass(frozen=True)
class SeedAsset:
    symbol: str
    company_name: Optional[str] = None
    sector: Optional[str] = None


@dataclass
class SeedResult:
    created: list[str]
    skipped: list[str]
    errors: list[str]


def parse_seed_assets(raw: Iterable[dict[str, Any]]) -> list[SeedAsset]:
    assets: list[SeedAsset] = []
    for index, row in enumerate(raw, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Seed row {index} must be an object")
        symbol = str(row.get("symbol") or "").strip().upper()
        if not symbol:
            raise ValueError(f"Seed row {index} is missing symbol")
        company_name = row.get("company_name")
        sector = row.get("sector")
        assets.append(
            SeedAsset(
                symbol=symbol,
                company_name=str(company_name).strip() if company_name else None,
                sector=str(sector).strip() if sector else None,
            )
        )
    return assets


def load_seed_file(path: Path | str) -> list[SeedAsset]:
    seed_path = Path(path)
    with seed_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"Seed file must contain a JSON array: {seed_path}")
    return parse_seed_assets(data)


def seed_tracked_assets(
    db: Session,
    assets: Iterable[SeedAsset],
    *,
    dry_run: bool = False,
) -> SeedResult:
    service = TrackedAssetsService(db)
    created: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    for asset in assets:
        existing = service.get_by_symbol(asset.symbol)
        if existing:
            skipped.append(asset.symbol)
            continue
        if dry_run:
            created.append(asset.symbol)
            continue
        try:
            service.create(asset.symbol, asset.company_name, asset.sector)
            created.append(asset.symbol)
        except ValueError as exc:
            errors.append(f"{asset.symbol}: {exc}")

    return SeedResult(created=created, skipped=skipped, errors=errors)
