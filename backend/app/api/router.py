from fastapi import APIRouter

from app.api.routes import alerts, articles, sentiment, tracked_assets

router = APIRouter(prefix="/api")
router.include_router(tracked_assets.router)
router.include_router(articles.router)
router.include_router(sentiment.router)
router.include_router(alerts.router)
