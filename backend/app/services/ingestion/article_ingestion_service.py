import logging
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set, Optional, Sequence

from app.core.config import settings
from app.core.timezone_util import now as app_now
from app.core.database import SessionLocal
from app.models.article import Articles

logger = logging.getLogger(__name__)


class ArticleIngestionService:
    """Fetch financial news from NewsAPI and dedupe against the database."""

    def __init__(self, news_api_key: Optional[str] = None, news_api_base_url: Optional[str] = None):
        self.news_api_key = news_api_key or settings.NEWS_API_KEY
        self.news_api_base_url = news_api_base_url or settings.NEWS_API_BASE_URL

        if not self.news_api_key:
            raise ValueError("News API key is required. Set NEWS_API_KEY in .env")
        if not self.news_api_base_url:
            raise ValueError("News API base URL is required. Set NEWS_API_BASE_URL in .env")

        self.news_api_endpoint = f"{self.news_api_base_url}/everything"
        self._request_headers = {"X-Api-Key": self.news_api_key}
        self.last_request_time = 0
        self.min_request_interval = 1.0
        self.max_retries = 3
        self.retry_delay = 2

        logger.info("Article Ingestion Service initialized")

    @staticmethod
    def build_date_range(
        hours_back: int,
        as_of: datetime | None = None,
    ) -> tuple[str, str]:
        """ISO datetimes for NewsAPI ``from`` / ``to`` params."""
        as_of = as_of or app_now()
        start = as_of - timedelta(hours=hours_back)
        return start.strftime("%Y-%m-%dT%H:%M:%S"), as_of.strftime("%Y-%m-%dT%H:%M:%S")

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _validate_article(self, article: Dict[str, Any]) -> bool:
        required_fields = ["title", "url", "publishedAt", "source"]
        if not all(field in article for field in required_fields):
            missing = [f for f in required_fields if f not in article]
            logger.warning(f"Article missing required fields: {missing}")
            return False
        if not article.get("url") or not article.get("title"):
            logger.warning(f"Article has empty URL or title: {article.get('url')}")
            return False
        return True

    def fetch_articles(
        self,
        query: str = "financial",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        max_pages: int = 10,
    ) -> List[Dict[str, Any]]:
        all_articles = []
        page = 1
        params = {
            "q": query,
            "sortBy": "publishedAt",
            "pageSize": 100,
        }
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        logger.info(f"Fetching articles with query: '{query}', pages: {max_pages}")

        seen_urls: Set[str] = set()

        while page <= max_pages:
            params["page"] = page
            self._rate_limit()
            articles: List[Dict[str, Any]] = []
            last_page = False

            for attempt in range(self.max_retries):
                try:
                    response = requests.get(
                        self.news_api_endpoint,
                        params=params,
                        headers=self._request_headers,
                        timeout=30,
                    )
                    response.raise_for_status()
                    data = response.json()

                    if data.get("status") == "error":
                        error_msg = data.get("message", "Unknown API error")
                        error_code = data.get("code", "")
                        if error_code == "maximumResultsReached":
                            logger.info(
                                "NewsAPI result cap reached at page %s (%s)",
                                page,
                                error_msg,
                            )
                            last_page = True
                            break
                        logger.error(f"NewsAPI error: {error_msg}")
                        if "rate limit" in error_msg.lower():
                            time.sleep(60)
                            continue
                        break

                    articles = data.get("articles", [])
                    if not articles:
                        logger.info(f"No more articles found at page {page}")
                        last_page = True
                        break

                    valid_articles = [a for a in articles if self._validate_article(a)]
                    added = 0
                    for article in valid_articles:
                        url = article.get("url")
                        if url and url in seen_urls:
                            continue
                        if url:
                            seen_urls.add(url)
                        all_articles.append(article)
                        added += 1

                    logger.info(
                        f"Page {page}: Fetched {len(articles)} articles "
                        f"({added} new, {len(valid_articles) - added} duplicate, "
                        f"{len(articles) - len(valid_articles)} invalid)"
                    )

                    if len(articles) < params["pageSize"]:
                        logger.info("Reached last page of results")
                        last_page = True
                        break

                    page += 1
                    break

                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:
                        time.sleep(60 * (attempt + 1))
                        continue
                    logger.error(f"HTTP error fetching articles: {e}")
                    if attempt == self.max_retries - 1:
                        break
                    time.sleep(self.retry_delay * (attempt + 1))

                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error fetching articles (attempt {attempt + 1}/{self.max_retries}): {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        break

                except Exception as e:
                    logger.error(f"Unexpected error fetching articles: {e}")
                    break

            if not articles or last_page:
                break

        logger.info(f"Total articles fetched: {len(all_articles)}")
        return all_articles

    def fetch_for_pipeline(
        self,
        *,
        query: str,
        from_date: str,
        to_date: str,
        max_pages: int,
        supplement_symbols: Sequence[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Broad query plus optional per-symbol searches, merged and URL-deduped.

        NewsAPI developer accounts cap each search at 100 results, so per-ticker
        fetches are the main way to pull more unique articles without a paid plan.
        """
        combined: List[Dict[str, Any]] = []
        seen_urls: Set[str] = set()

        def merge(batch: List[Dict[str, Any]], label: str) -> None:
            added = 0
            for article in batch:
                url = article.get("url")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                combined.append(article)
                added += 1
            logger.info("Merged %s new articles from %s (%s total unique)", added, label, len(combined))

        merge(
            self.fetch_articles(
                query=query,
                from_date=from_date,
                to_date=to_date,
                max_pages=max_pages,
            ),
            f"query '{query}'",
        )

        if supplement_symbols:
            for symbol in supplement_symbols:
                merge(
                    self.fetch_articles(
                        query=symbol,
                        from_date=from_date,
                        to_date=to_date,
                        max_pages=1,
                    ),
                    f"symbol {symbol}",
                )

        logger.info("Pipeline fetch complete: %s unique articles", len(combined))
        return combined

    def _get_existing_urls(self, article_urls: List[str]) -> Set[str]:
        if not article_urls:
            return set()

        db = SessionLocal()
        try:
            existing_articles = db.query(Articles.url).filter(
                Articles.url.in_(article_urls)
            ).all()
            return {url[0] for url in existing_articles}
        except Exception as e:
            logger.error(f"Error checking existing articles: {e}")
            return set()
        finally:
            db.close()

    def filter_new_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Return validated articles whose URLs are not already in Postgres.
        """
        if not articles:
            return []

        valid = [a for a in articles if self._validate_article(a)]
        urls = [a["url"] for a in valid if a.get("url")]
        if not urls:
            return []

        existing = self._get_existing_urls(urls)
        new_articles = [a for a in valid if a["url"] not in existing]
        logger.info(
            f"Filtered {len(new_articles)} new articles "
            f"({len(existing)} duplicates, {len(articles) - len(valid)} invalid)"
        )
        return new_articles
