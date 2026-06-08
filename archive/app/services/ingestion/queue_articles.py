"""
Archived Celery/Redis article queueing (removed from active ingestion service).

Reference copy from the pre-cron architecture. Imports assume the old app layout.
"""

import json
import logging
from typing import Any, Dict, List, Set

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.article import Articles

logger = logging.getLogger(__name__)


def _get_existing_urls(article_urls: List[str]) -> Set[str]:
    if not article_urls:
        return set()
    db = SessionLocal()
    try:
        existing_articles = db.query(Articles.url).filter(Articles.url.in_(article_urls)).all()
        return {url[0] for url in existing_articles}
    except Exception as e:
        logger.error(f"Error checking existing articles: {e}")
        return set()
    finally:
        db.close()


def queue_articles(
    articles: List[Dict[str, Any]],
    use_celery: bool = True,
    validate_article=None,
) -> Dict[str, int]:
    if not articles:
        return {"total": 0, "new": 0, "duplicates": 0, "invalid": 0, "failed": 0}

    valid_articles = []
    invalid_count = 0
    for article in articles:
        if validate_article is None or validate_article(article):
            valid_articles.append(article)
        else:
            invalid_count += 1

    if not valid_articles:
        return {
            "total": len(articles),
            "new": 0,
            "duplicates": 0,
            "invalid": invalid_count,
            "failed": 0,
        }

    article_urls = []
    url_to_article = {}
    for article in valid_articles:
        url = article.get("url")
        if url:
            article_urls.append(url)
            url_to_article[url] = article

    if not article_urls:
        return {
            "total": len(articles),
            "new": 0,
            "duplicates": 0,
            "invalid": invalid_count,
            "failed": 0,
        }

    existing_urls = _get_existing_urls(article_urls)
    new_articles = [url_to_article[url] for url in article_urls if url not in existing_urls]

    queued_count = 0
    failed_count = 0

    if use_celery:
        try:
            from app.workers.celery_worker import process_article_task

            for article in new_articles:
                try:
                    process_article_task.delay(article)
                    queued_count += 1
                except Exception as e:
                    logger.error(f"Error queuing article {article.get('url', 'unknown')}: {e}")
                    failed_count += 1
        except ImportError:
            logger.error("Celery worker task not found, falling back to Redis")
            use_celery = False

    if not use_celery:
        from redis import Redis

        redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )
        for article in new_articles:
            try:
                redis_client.lpush("article_queue", json.dumps(article))
                queued_count += 1
            except Exception as e:
                logger.error(f"Error queuing article {article.get('url', 'unknown')}: {e}")
                failed_count += 1

    return {
        "total": len(articles),
        "new": queued_count,
        "duplicates": len(existing_urls),
        "invalid": invalid_count,
        "failed": failed_count,
    }
