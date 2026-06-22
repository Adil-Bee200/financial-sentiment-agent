# Financial Sentiment Agent

Automated financial news ingestion, LLM sentiment analysis, and a live dashboard for tracked equities.

**Live demo:** https://tubular-lolly-084b55.netlify.app

---

## At a glance

| | |
|---|---|
| **Scale** | 10 tracked equities · daily automated pipeline · 280+ articles ingested per run |
| **LLM budget** | Hard cap of **80 OpenAI calls/day** (prod) · typical run analyzes **~60** after keyword filter |
| **LLM efficiency** | ~14% of fetched articles reach OpenAI · ~$0.05 per run · ~$1.50/month at daily cadence |
| **Stack** | Python 3.12 · FastAPI · PostgreSQL (Neon) · OpenAI · GitHub Actions · React 19 · TypeScript |
| **Quality** | 107 automated tests (99 backend · 8 frontend) · ~73% backend coverage · full-stack CI on every push · daily production smoke test |
| **Deploy** | Render (API) · Netlify (dashboard) · Neon (database) |

### Typical production run

| Metric | Value |
|--------|------:|
| Articles fetched (NewsAPI) | ~286 |
| Passed keyword filter | ~72 (~25%) |
| LLM-analyzed & stored | ~60 (~14% of fetched; **under 80/day cap**) |
| LLM budget (configured max) | 80 articles / day |
| Run duration | ~4 min |
| Estimated OpenAI cost | ~$0.05 |
| Alerts triggered | ~6 |

Most fetched articles never reach OpenAI, keyword confidence scoring (≥ 0.90) and priority ranking gate them first. The **80/day cap** is a cost ceiling; typical runs don't reach it.

---

## Overview

This project watches a portfolio of major US equities, pulls financial news every day, and scores how positive or negative the coverage is using OpenAI. Results land in PostgreSQL, roll up into daily sentiment trends, and can trigger alerts when sentiment or article volume spikes.

On the read side, a FastAPI backend serves the data and a React dashboard lets you explore sentiment gauges, 7-day rolling sentiment, charts, recent articles, and pipeline status for each ticker.

**Pipeline flow:**

1. Fetch financial news from NewsAPI (48h window, general + per-ticker queries)
2. Dedupe by URL and filter to tracked tickers with keyword confidence scoring (≥ 0.90)
3. Rank by priority and send top articles to OpenAI (`gpt-5-mini`) under a **daily budget of 80 LLM calls** (production)
4. Store summaries, sentiment scores (−1…+1), and roll up daily sentiment by analysis day (US Eastern)
5. Evaluate rolling sentiment and volume-spike rules; notify via optional Discord webhooks
6. Serve everything through a read-only REST API and React dashboard

**Tracked tickers:** NVDA · AAPL · MSFT · GOOGL · AMZN · META · TSLA · JPM · BAC · GS

---

## Screenshots

**Dashboard** : sidebar, header, and sentiment gauge for the selected ticker.

![Dashboard](./docs/screenshots/dashboard.png)

**Charts** : momentum and 7-day sentiment & volume.

![Charts](./docs/screenshots/charts.png)

**Articles** : recent news feed with LLM summaries and sentiment scores.

![Articles](./docs/screenshots/articles.png)

**Pipeline** : latest run status and alerts panel.

![Pipeline](./docs/screenshots/pipeline.png)

---

## Architecture

```mermaid
flowchart TB
    subgraph Schedule["GitHub Actions (daily cron)"]
        CRON["21:00 UTC cron"]
        PIPE["run_pipeline.py"]
        CRON --> PIPE
    end

    subgraph External["External services"]
        NEWS["NewsAPI"]
        OAI["OpenAI API"]
        DISCORD["Discord webhook"]
    end

    subgraph Data["Neon PostgreSQL"]
        DB[("articles · sentiment_daily · alerts · processing_runs")]
    end

    subgraph API["Render — FastAPI"]
        REST["/api/* read-only REST"]
    end

    subgraph UI["Netlify — React SPA"]
        DASH["Dashboard"]
    end

    PIPE --> NEWS
    PIPE --> OAI
    PIPE --> DB
    PIPE --> DISCORD
    REST --> DB
    DASH --> REST
```

---

## Tech stack

| Layer | Technologies |
|-------|----------------|
| **Pipeline** | Python 3.12, SQLAlchemy, Alembic, NewsAPI, OpenAI SDK |
| **API** | FastAPI, Uvicorn, Pydantic v2, SlowAPI rate limiting |
| **Database** | PostgreSQL (Neon), UUID hub schema, pooled connections |
| **Orchestration** | GitHub Actions (full-stack CI, daily pipeline cron, production smoke test) |
| **Frontend** | React 19, TypeScript, Vite 8, Tailwind CSS v4, Recharts |
| **Deploy** | Render (API), Netlify (UI), GitHub Secrets (pipeline env) |

---

## Data flow

### Pipeline (write path)

```mermaid
sequenceDiagram
    participant GH as GitHub Actions
    participant P as PipelineService
    participant N as NewsAPI
    participant L as OpenAI
    participant DB as Postgres

    GH->>P: run_pipeline()
    P->>N: fetch articles (48h window)
    P->>P: dedupe by URL
    P->>P: keyword filter + priority score
    loop Up to daily LLM cap
        P->>L: analyze_article(title, body)
        L-->>P: sentiment + summary
        P->>DB: articles + article_entities
    end
    P->>DB: sentiment_daily rollup (analysis day ET)
    P->>DB: alerts + processing_runs
```

| Step | Description |
|------|-------------|
| **Fetch** | General financial query + per-ticker NewsAPI supplement |
| **Dedupe** | Skip URLs already in `articles` |
| **Filter** | Map articles to tickers via keyword confidence (≥ 0.90) |
| **Rank** | Priority score gates LLM budget — newest, most relevant first |
| **Analyze** | LLM returns structured sentiment (−1…+1) and summary |
| **Roll up** | Daily `sentiment_daily` keyed by `processed_at` calendar day (ET) |
| **Alert** | 7-day rolling sentiment + volume spike rules; optional Discord |

### Dashboard (read path)

```mermaid
sequenceDiagram
    participant UI as React dashboard
    participant API as FastAPI (Render)
    participant DB as Postgres

    UI->>API: GET /api/tracked-assets
    UI->>API: GET /api/sentiment/daily?days=7
    UI->>API: GET /api/pipeline/status
    UI->>API: GET /api/alerts
    UI->>API: GET /api/articles?symbol=NVDA
    API->>DB: query
    DB-->>API: rows
    API-->>UI: canonical JSON (analysis_date, labels, etc.)
```

The frontend **does not recompute calendar buckets** — dates and ET labels come from the API.

---

## Deployment

[![CI](https://github.com/Adil-Bee200/financial-sentiment-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Adil-Bee200/financial-sentiment-agent/actions/workflows/ci.yml)
[![Pipeline](https://github.com/Adil-Bee200/financial-sentiment-agent/actions/workflows/pipeline.yml/badge.svg)](https://github.com/Adil-Bee200/financial-sentiment-agent/actions/workflows/pipeline.yml)
[![Smoke test](https://github.com/Adil-Bee200/financial-sentiment-agent/actions/workflows/smoke.yml/badge.svg)](https://github.com/Adil-Bee200/financial-sentiment-agent/actions/workflows/smoke.yml)

| | |
|---|---|
| **API** | [financial-sentiment-agent.onrender.com](https://financial-sentiment-agent.onrender.com) |
| **API docs** | [OpenAPI / Swagger](https://financial-sentiment-agent.onrender.com/docs) |
| **Dashboard** | Deploy frontend to Netlify (see below) |

```mermaid
flowchart LR
    subgraph Dev["Developer"]
        GIT["GitHub repo"]
    end

    subgraph GHA["GitHub Actions"]
        CI["ci.yml — backend + frontend"]
        PL["pipeline.yml — daily cron"]
        SM["smoke.yml — live API check"]
    end

    subgraph Prod["Production"]
        NEON[("Neon Postgres")]
        RENDER["Render Web Service<br/>FastAPI"]
        NETLIFY["Netlify<br/>React static site"]
    end

    GIT --> CI
    GIT --> PL
    SM --> RENDER
    PL --> NEON
    RENDER --> NEON
    NETLIFY --> RENDER
```

| Service | Role | Config |
|---------|------|--------|
| **GitHub Actions** | CI (pytest + Vitest), daily pipeline, production smoke test | `DATABASE_URL`, `OPENAI_API_KEY`, `NEWS_API_KEY`, `DISCORD_WEBHOOK_URL` |
| **Neon** | Primary datastore | Pooled `DATABASE_URL` |
| **Render** | Read-only API | Root: `backend`, start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Netlify** | Frontend SPA | Base: `frontend`, publish: `dist`, `VITE_API_URL` → Render URL |

**Render env (minimum):** `DATABASE_URL`

**Netlify env:** `VITE_API_URL=https://your-api.onrender.com`

---

## API reference

Base URL: `https://financial-sentiment-agent.onrender.com`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | API + DB connectivity |
| `GET` | `/api/tracked-assets` | Monitored tickers |
| `GET` | `/api/sentiment/daily` | Analysis-day rollups with 7-day rolling sentiment (`?symbol=&days=`) |
| `GET` | `/api/articles` | Articles for one ticker (`?symbol=` required) |
| `GET` | `/api/alerts` | Recent alerts |
| `GET` | `/api/pipeline/status` | Latest run metrics (duration, tokens, cost) |
| `GET` | `/api/stats` | Aggregate project metrics (averages, totals, filter rates) |

Interactive docs: [`/docs`](https://financial-sentiment-agent.onrender.com/docs)

### Example responses

**`GET /api/tracked-assets`**

```json
[
  {
    "ticker_id": "dd81700f-6dc0-431d-a54d-8e298d159776",
    "symbol": "NVDA",
    "company_name": "NVIDIA Corporation",
    "sector": "Technology",
    "created_at": "2026-06-14T05:30:13.386335Z"
  }
]
```

**`GET /api/sentiment/daily?symbol=NVDA&days=7`**

```json
[
  {
    "symbol": "NVDA",
    "analysis_date": "2026-06-17",
    "analysis_date_label": "Wed, Jun 17",
    "chart_axis_label": "Wed",
    "timezone": "America/New_York",
    "avg_sentiment": 0.291,
    "article_count": 11,
    "momentum": 0.042,
    "rolling_7d_sentiment": 0.18,
    "std_div": 0.18,
    "last_run_at": "2026-06-17T22:33:57.340828Z",
    "is_current_analysis_day": true
  }
]
```

**`GET /api/articles?symbol=NVDA&limit=1`**

```json
[
  {
    "article_id": "290069a1-bf54-4180-92b3-b096cfa564a5",
    "title": "Nvidia's Jensen Huang says society needs 'new social norms' in the age of AI",
    "source": "Japan Today",
    "url": "https://example.com/article",
    "published_at": "2026-06-16T21:44:20Z",
    "analyzed_at": "2026-06-17T22:33:23.700000Z",
    "published_at_label": "Jun 16, 5:44 PM ET",
    "analyzed_at_label": "Jun 17, 6:33 PM ET",
    "summary": "Nvidia CEO Jensen Huang says society must adopt new social norms as AI advances.",
    "symbol": "NVDA",
    "sentiment_score": 0.5,
    "confidence": 0.92,
    "relevance_score": 0.92
  }
]
```

**`GET /api/pipeline/status`**

```json
{
  "run_id": "d82f283d-ce2f-466c-9819-49037e6a6d0f",
  "status": "completed",
  "last_run_at": "2026-06-17T22:33:57.340828Z",
  "started_at": "2026-06-17T22:30:04.728530Z",
  "timezone": "America/New_York",
  "articles_fetched": 286,
  "articles_keyword_matched": 72,
  "articles_analyzed": 39,
  "articles_skipped_llm_limit": 33,
  "run_duration_seconds": 234.0,
  "estimated_llm_cost": 0.05,
  "llm_prompt_tokens": 142000,
  "llm_completion_tokens": 28000,
  "alerts_triggered": 6
}
```

**`GET /api/stats`**

```json
{
  "tracked_tickers": 10,
  "completed_pipeline_runs": 12,
  "total_articles_stored": 97,
  "total_ticker_mentions": 120,
  "total_alerts": 18,
  "total_articles_analyzed": 56,
  "total_estimated_llm_cost_usd": 0.58,
  "recent_runs_sample_size": 10,
  "avg_articles_fetched": 286.0,
  "avg_articles_keyword_matched": 72.0,
  "avg_articles_analyzed": 39.0,
  "avg_run_duration_seconds": 234.0,
  "avg_estimated_llm_cost_usd": 0.05,
  "llm_selectivity_pct": 54.2,
  "keyword_filter_pass_rate_pct": 25.2,
  "estimated_monthly_llm_cost_usd": 1.5
}
```

**`GET /health`**

```json
{
  "status": "ok",
  "database": "connected"
}
```

---

## Local development

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL (or Neon connection string)
- NewsAPI and OpenAI API keys (pipeline only)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env                # edit DATABASE_URL, API keys
alembic upgrade head
python -m scripts.seed_assets
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

### Tests

**Backend** (pytest):

```bash
cd backend && pytest
```

**Frontend** (Vitest):

```bash
cd frontend && npm test
```

CI runs both suites in parallel on every push to `backend/`, `frontend/`, or workflow changes. A separate **production smoke test** (`smoke.yml`) hits the live Render API daily (with retries for cold starts) and can be triggered manually from the Actions tab.

### Run pipeline manually

```bash
cd backend
source .venv/bin/activate
python -m scripts.run_pipeline
```

### Recompute sentiment rollups

```bash
python -m scripts.reaggregate_sentiment --days 7
```

### Print live stats (for README updates)

```bash
python -m scripts.print_project_stats
```

---

## Project structure

```
financial-sentiment-agent/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # config, DB, timezone utilities
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # pipeline, LLM, sentiment, alerts
│   │   └── schemas/          # Pydantic response models
│   ├── alembic/              # migrations
│   ├── scripts/              # run_pipeline, seed_assets, reaggregate
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── api/              # typed API client
│   │   ├── components/       # dashboard UI
│   │   └── hooks/            # useDashboard
│   └── netlify.toml
├── .github/workflows/
│   ├── ci.yml                # backend pytest + frontend lint/test/build
│   ├── pipeline.yml          # daily news pipeline
│   └── smoke.yml             # daily production API smoke test
└── docs/screenshots/         # README images
```

---

## Design notes

- **Analysis day (ET):** Daily sentiment is grouped by when articles were *analyzed* (`processed_at`), not when they were published — so the gauge matches each pipeline run’s calendar day.
- **7-day rolling sentiment:** Article-weighted rolling average over the last 7 analysis days — same formula as alert rules. Exposed on `GET /api/sentiment/daily` and shown in the dashboard next to day-over-day momentum.
- **Pipeline metrics:** Each run records fetch/filter/analyze counts, LLM tokens, estimated cost, and duration in `processing_runs`. Aggregates are served by `GET /api/pipeline/status` and `GET /api/stats`.
- **LLM budget:** Per-run and per-day caps with priority scoring limit OpenAI cost.
- **Cold starts:** The Netlify UI loads immediately and retries while the Render free-tier API wakes up.

---

## Further reading

- [backend/SETUP.md](backend/SETUP.md) — backend env, timezone, migrations
- [frontend/README.md](frontend/README.md) — frontend-specific setup
- [docs/screenshots/README.md](docs/screenshots/README.md) — how to add README images

---

## License

MIT — see repository for details.
