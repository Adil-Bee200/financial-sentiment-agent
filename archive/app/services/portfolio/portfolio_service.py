import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from redis import Redis

from app.models.portfolio import Portfolio, PortfolioTickers
from app.core.config import settings

logger = logging.getLogger(__name__)

CACHE_KEY_ALL_TICKERS = "tracked_tickers:all"
CACHE_KEY_USER_TICKERS = "tracked_tickers:user:{}"
CACHE_TTL = 300


class PortfolioService:
    """Archived version with optional Redis ticker cache."""

    def __init__(self, db: Session, redis_client: Optional[Redis] = None):
        self.db = db
        self._redis_client = redis_client
        self._redis_initialized = False

    def _get_redis_client(self) -> Optional[Redis]:
        if self._redis_client is not None:
            return self._redis_client
        if not self._redis_initialized:
            try:
                self._redis_client = Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                )
                self._redis_client.ping()
                self._redis_initialized = True
            except Exception as e:
                logger.warning(f"Redis cache unavailable: {e}. Continuing without cache.")
                self._redis_client = None
                self._redis_initialized = True
        return self._redis_client

    def _invalidate_ticker_cache(self):
        redis = self._get_redis_client()
        if redis:
            try:
                keys = redis.keys("tracked_tickers:*")
                if keys:
                    redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Error invalidating cache: {e}")

    def get_all_tracked_tickers(self) -> List[str]:
        redis = self._get_redis_client()
        if redis:
            try:
                cached = redis.get(CACHE_KEY_ALL_TICKERS)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache read error: {e}. Falling back to database.")
        tickers_result = self.db.query(PortfolioTickers.ticker).distinct().all()
        tickers = [ticker[0] for ticker in tickers_result]
        if redis:
            try:
                redis.setex(CACHE_KEY_ALL_TICKERS, CACHE_TTL, json.dumps(tickers))
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
        return tickers
