from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.models.tracked_assets import TrackedAssets
from app.seeds.loader import (
    DEFAULT_SEED_FILE,
    SeedAsset,
    load_seed_file,
    parse_seed_assets,
    seed_tracked_assets,
)


class TestSeedLoader:
    def test_default_seed_file_exists_and_parses(self):
        assets = load_seed_file(DEFAULT_SEED_FILE)
        assert len(assets) >= 3
        symbols = {asset.symbol for asset in assets}
        assert {"NVDA", "AAPL", "MSFT"}.issubset(symbols)

    def test_parse_seed_assets_requires_symbol(self):
        with pytest.raises(ValueError, match="missing symbol"):
            parse_seed_assets([{"company_name": "No symbol"}])

    def test_load_seed_file_rejects_non_array(self, tmp_path: Path):
        seed_file = tmp_path / "bad.json"
        seed_file.write_text('{"symbol": "NVDA"}', encoding="utf-8")
        with pytest.raises(ValueError, match="JSON array"):
            load_seed_file(seed_file)

    def test_seed_tracked_assets_creates_missing_only(self):
        db = Mock()
        existing = TrackedAssets(ticker_id=uuid4(), symbol="NVDA")
        created_asset = TrackedAssets(ticker_id=uuid4(), symbol="AAPL")

        service = Mock()
        service.get_by_symbol.side_effect = lambda symbol: existing if symbol == "NVDA" else None
        service.create.return_value = created_asset

        assets = [
            SeedAsset(symbol="NVDA", company_name="NVIDIA Corporation"),
            SeedAsset(symbol="AAPL", company_name="Apple Inc"),
        ]

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr("app.seeds.loader.TrackedAssetsService", lambda _db: service)
            result = seed_tracked_assets(db, assets)

        assert result.created == ["AAPL"]
        assert result.skipped == ["NVDA"]
        assert result.errors == []
        service.create.assert_called_once_with("AAPL", "Apple Inc", None)

    def test_seed_tracked_assets_dry_run_does_not_write(self):
        db = Mock()
        service = Mock()
        service.get_by_symbol.return_value = None

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr("app.seeds.loader.TrackedAssetsService", lambda _db: service)
            result = seed_tracked_assets(
                db,
                [SeedAsset(symbol="MSFT", company_name="Microsoft Corporation")],
                dry_run=True,
            )

        assert result.created == ["MSFT"]
        assert result.skipped == []
        service.create.assert_not_called()
