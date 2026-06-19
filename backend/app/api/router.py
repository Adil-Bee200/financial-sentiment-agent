from fastapi import APIRouter

from app.api.routes import alerts, articles, pipeline, sentiment, stats, tracked_assets

router = APIRouter(prefix="/api")
router.include_router(tracked_assets.router)
router.include_router(articles.router)
router.include_router(sentiment.router)
router.include_router(alerts.router)
router.include_router(pipeline.router)
router.include_router(stats.router)
