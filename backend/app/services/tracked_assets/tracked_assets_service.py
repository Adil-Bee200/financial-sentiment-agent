from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.timezone_util import now as app_now
from app.models.tracked_assets import TrackedAssets


class TrackedAssetsService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, symbol: str, company_name: Optional[str] = None, sector: Optional[str] = None) -> TrackedAssets:
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("Symbol cannot be empty")
        existing = self.get_by_symbol(symbol)
        if existing:
            raise ValueError(f"Symbol already tracked: {symbol}")
        asset = TrackedAssets(
            symbol=symbol,
            company_name=company_name,
            sector=sector,
            created_at=app_now(),
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def get_by_id(self, ticker_id: UUID) -> TrackedAssets:
        asset = self.db.query(TrackedAssets).filter(TrackedAssets.ticker_id == ticker_id).first()
        if not asset:
            raise LookupError("Tracked asset not found")
        return asset

    def get_by_symbol(self, symbol: str) -> Optional[TrackedAssets]:
        return (
            self.db.query(TrackedAssets)
            .filter(TrackedAssets.symbol == symbol.strip().upper())
            .first()
        )

    def require_by_symbol(self, symbol: str) -> TrackedAssets:
        asset = self.get_by_symbol(symbol)
        if not asset:
            raise LookupError(f"Tracked asset not found: {symbol}")
        return asset

    def list_all(self) -> List[TrackedAssets]:
        return self.db.query(TrackedAssets).order_by(TrackedAssets.symbol).all()

    def get_all_symbols(self) -> List[str]:
        rows = self.db.query(TrackedAssets.symbol).order_by(TrackedAssets.symbol).all()
        return [row[0] for row in rows]

    def delete(self, symbol: str) -> None:
        asset = self.require_by_symbol(symbol)
        self.db.delete(asset)
        self.db.commit()
