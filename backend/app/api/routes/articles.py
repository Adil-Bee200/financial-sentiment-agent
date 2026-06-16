from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.limiter import limiter
from app.models.article import ArticleEntities, Articles
from app.models.tracked_assets import TrackedAssets
from app.schemas.api import ArticleResponse

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=list[ArticleResponse])
@limiter.limit("60/minute")
def list_articles(
    request: Request,
    symbol: Optional[str] = Query(default=None, description="Filter by ticker symbol"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Articles, ArticleEntities, TrackedAssets)
        .join(ArticleEntities, Articles.article_id == ArticleEntities.article_id)
        .join(TrackedAssets, ArticleEntities.ticker_id == TrackedAssets.ticker_id)
    )
    if symbol:
        query = query.filter(TrackedAssets.symbol == symbol.upper())

    rows = query.order_by(Articles.published_at.desc()).limit(limit).all()
    return [
        ArticleResponse(
            article_id=article.article_id,
            title=article.title,
            source=article.source,
            url=article.url,
            published_at=article.published_at,
            summary=article.summary,
            symbol=asset.symbol,
            sentiment_score=entity.sentiment_score,
            confidence=entity.confidence,
        )
        for article, entity, asset in rows
    ]
