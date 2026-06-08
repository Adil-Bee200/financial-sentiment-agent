"""
Celery Worker Tasks for Article Processing

This module contains Celery tasks for processing articles:
1. process_article_task - Main task to process a single article
2. fetch_and_queue_articles_task - Scheduled task to fetch and queue articles
"""

import logging
from datetime import datetime, timedelta
from app.core.celery_app import celery_app
from app.services.ingestion.article_ingestion_service import ArticleIngestionService
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(name="process_article", bind=True, max_retries=3)
def process_article_task(self, article_data: dict):
    try:
        logger.info(f"Processing article: {article_data.get('title', 'Unknown')}")
        logger.info(f"Article processed: {article_data.get('url')}")
        return {"status": "success", "article_url": article_data.get('url')}
    except Exception as e:
        logger.error(f"Error processing article {article_data.get('url', 'unknown')}: {e}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@celery_app.task(name="fetch_and_queue_articles")
def fetch_and_queue_articles_task(query: str = "financial", hours_back: int = 24):
    try:
        logger.info(f"Starting scheduled article fetch: query='{query}', hours_back={hours_back}")
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(hours=hours_back)
        from_date_str = from_date.strftime("%Y-%m-%d")
        to_date_str = to_date.strftime("%Y-%m-%d")
        service = ArticleIngestionService()
        articles = service.fetch_articles(
            query=query,
            from_date=from_date_str,
            to_date=to_date_str,
            max_pages=10,
        )
        if not articles:
            return {"status": "success", "articles_fetched": 0}
        result = service.queue_articles(articles, use_celery=True)
        return {"status": "success", "articles_fetched": len(articles), "queue_result": result}
    except Exception as e:
        logger.error(f"Error in scheduled article fetch: {e}")
        return {"status": "error", "error": str(e)}
