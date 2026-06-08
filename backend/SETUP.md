# Backend setup

Cron-based pipeline (GitHub Actions + Postgres + OpenAI). Legacy Celery/FastAPI code is in `archive/`.

## Environment

From this directory (`backend/`):

```bash
cp env.example .env
```

Required: `DATABASE_URL`, `OPENAI_API_KEY`, `NEWS_API_KEY`  
Optional: `DISCORD_WEBHOOK_URL`

## Database

```bash
alembic upgrade head
```

Use Neon’s **pooled** connection string in production.

## Tests

```bash
pytest
```

## Next

Implement `scripts/run_pipeline.py` and `.github/workflows/pipeline.yml` (2–4×/day cron).
