from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import nullslast
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
    symbol: str = Query(..., min_length=1, description="Tracked ticker symbol (required)"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Latest articles for one tracked ticker, newest first."""
    normalized = symbol.strip().upper()
    asset = db.query(TrackedAssets).filter(TrackedAssets.symbol == normalized).first()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Tracked asset not found: {normalized}")

    rows = (
        db.query(Articles, ArticleEntities)
        .join(ArticleEntities, Articles.article_id == ArticleEntities.article_id)
        .filter(ArticleEntities.ticker_id == asset.ticker_id)
        .order_by(
            Articles.published_at.desc(),
            nullslast(ArticleEntities.relevance_score.desc()),
            ArticleEntities.confidence.desc(),
        )
        .limit(limit)
        .all()
    )
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
            relevance_score=entity.relevance_score,
        )
        for article, entity in rows
    ]
