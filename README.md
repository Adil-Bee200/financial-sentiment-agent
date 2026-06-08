# Financial Research Agent

Monorepo for an autonomous financial news pipeline: fetch articles, filter by portfolio tickers, analyze sentiment with OpenAI, store results in Postgres, and send Discord alerts.

## Structure

```
├── backend/     Python pipeline, services, DB migrations, tests, archive/
├── frontend/    UI (not started)
└── README.md
```

## Quick start

Use **one venv inside `backend/`** only (do not create `.venv` at the repo root).

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp env.example .env      # then edit credentials
alembic upgrade head
pytest
```

If you still have an old `Financial-agent/.venv` at the repo root, delete it — it pointed at the pre-restructure layout.

See [backend/SETUP.md](backend/SETUP.md) for details.

## Deployment (planned)

GitHub Actions cron (2–4×/day) → `backend/scripts/run_pipeline.py` → Neon Postgres → OpenAI → Discord.
