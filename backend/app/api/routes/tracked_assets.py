from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.limiter import limiter
from app.models.tracked_assets import TrackedAssets
from app.schemas.api import TrackedAssetResponse

router = APIRouter(prefix="/tracked-assets", tags=["tracked-assets"])


@router.get("", response_model=list[TrackedAssetResponse])
@limiter.limit("60/minute")
def list_tracked_assets(request: Request, db: Session = Depends(get_db)):
    assets = db.query(TrackedAssets).order_by(TrackedAssets.symbol).all()
    return assets
