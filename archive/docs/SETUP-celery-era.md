# Core Infrastructure Setup Guide (Celery era)

Archived from root `SETUP.md` when moving to the GitHub Actions cron pipeline.

## What was set up

1. **Core Configuration** — Database, Redis, Celery, OpenAI, Discord, News API
2. **Database Layer** — SQLAlchemy + Alembic
3. **Models** — User, Portfolio, Articles, SentimentDaily, Alerts
4. **FastAPI** — `archive/app/main.py` (health only)
5. **Celery** — `archive/app/workers/`, Beat every 5 minutes

## Old run commands

```bash
uvicorn app.main:app --reload
celery -A app.core.celery_app worker --loglevel=info
celery -A app.core.celery_app beat --loglevel=info
```

See `archive/requirements-celery.txt` for restored dependencies.
