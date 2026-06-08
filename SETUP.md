# Financial Research Agent — Setup

Cron-based pipeline (GitHub Actions + Postgres + OpenAI). Celery/FastAPI code lives under `archive/`.

## Environment

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

## Run tests

```bash
pytest
```

## Next

Implement `scripts/run_pipeline.py` and `.github/workflows/pipeline.yml` (2–4×/day cron).
