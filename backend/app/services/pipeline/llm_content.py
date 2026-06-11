"""Shape article text for LLM calls and track daily LLM usage."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.article import ArticleEntities


def truncate_at_word(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0]
    return cut + "..." if cut else text[:max_chars] + "..."


def build_llm_input(article: dict, body_max_chars: int | None = None) -> tuple[str, str]:
    """
    Build (title, content) for the LLM.

    Content is description plus up to ``body_max_chars`` from the article body.
    Title is passed separately and is not counted toward the body limit.
    """
    limit = body_max_chars if body_max_chars is not None else settings.LLM_BODY_MAX_CHARS
    title = (article.get("title") or "").strip()
    description = (article.get("description") or "").strip()
    body = (article.get("content") or "").strip()

    if body:
        body = truncate_at_word(body, limit)

    parts = [p for p in (description, body) if p]
    content = "\n\n".join(parts)
    return title, content


def count_llm_articles_today(db: Session, as_of: datetime | None = None) -> int:
    """Distinct articles that received LLM processing today (UTC)."""
    as_of = as_of or datetime.now(timezone.utc)
    day_start = datetime.combine(as_of.date(), datetime.min.time(), tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)
    return (
        db.query(func.count(func.distinct(ArticleEntities.article_id)))
        .filter(
            ArticleEntities.processed_at >= day_start,
            ArticleEntities.processed_at < day_end,
        )
        .scalar()
        or 0
    )


def remaining_llm_budget(db: Session, as_of: datetime | None = None) -> int:
    as_of = as_of or datetime.now(timezone.utc)
    used = count_llm_articles_today(db, as_of)
    return max(0, settings.MAX_LLM_ARTICLES_PER_DAY - used)
