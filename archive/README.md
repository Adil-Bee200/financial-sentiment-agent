# Archive

Code from the **Celery + Redis + FastAPI** architecture, kept for reference while the project moves to a **GitHub Actions cron pipeline**.

Not imported by the active app. Paths under `archive/app/` mirror the old layout.

| Path | What it was |
|------|-------------|
| `app/workers/celery_worker.py` | Celery tasks (`process_article`, `fetch_and_queue_articles`) |
| `app/core/celery_app.py` | Celery app + Beat schedule (every 5 min) |
| `app/main.py` | FastAPI app (`/` and `/health` only) |
| `app/api/` | Empty API routes package |
| `app/services/ingestion/queue_articles.py` | Celery/Redis article queueing |
| `app/services/portfolio/portfolio_service.py` | Portfolio service with Redis ticker cache |
| `requirements-celery.txt` | Extra deps for the old stack (celery, redis, fastapi) |

## Active app (unchanged location)

- `app/models/`, `app/schemas/`, `app/core/` (config + database)
- `app/services/` — alerts, ingestion, llm, portfolio, sentiment
- `alembic/`, `tests/`

Next: `scripts/run_pipeline.py` + GitHub Actions workflow.
