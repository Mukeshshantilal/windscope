# WindScope

Wind energy generation forecasting and accuracy analysis for UK electricity purchasing teams.

WindScope is a full-stack analytics application that compares Elexon national wind outturn with the wind forecasts that were actually available when day-ahead purchasing decisions were made.

## Business problem

A UK energy utility buys electricity in the wholesale day-ahead market. Before those purchases, the team needs to know:

- How much wind generation is expected
- What wind generation actually occurred
- How accurate the forecasts were
- How much uncertainty sits in the errors
- Which forecast revision was available at decision time, not the latest revision published after the cutoff

The product uses only UK national wind actuals and forecasts from Elexon. It does not use price, demand, or weather APIs.

## Features

- Overview dashboard with KPI cards, forecast vs actual chart, daily error, coverage, and worst days
- Generation analysis with daily / hourly / half-hourly views, sortable table, and CSV export
- Forecast accuracy: MAE, RMSE, bias, MAPE (with zero-actual handling), histogram, hour-of-day, and percentiles
- Forecast explorer for point-in-time revisions against a delivery hour
- Data quality and methodology page that separates observed facts from assumptions
- Idempotent historical import from the official Elexon BMRS API
- PostgreSQL storage of actuals and every forecast revision

## Technology stack

**Frontend:** React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Recharts, TanStack Query, Axios, Lucide React, React Router

**Backend:** Python 3.12+, FastAPI, Pydantic, Pandas, NumPy, HTTPX, SQLAlchemy, PostgreSQL

**Infrastructure:** Docker, Docker Compose, environment variables, Vercel-ready frontend, Render/Heroku-ready API

## Architecture

```
Browser  →  Vite / nginx SPA  →  FastAPI  →  PostgreSQL
                                   ↑
                             Elexon BMRS (import only)
```

Request paths read imported historical data. The live Elexon API is used by the import command, not by dashboard queries.

## Folder structure

```
backend/           FastAPI application, Alembic, tests
frontend/          React SPA
docker-compose.yml PostgreSQL, API, web UI, optional importer
.env.example       Environment template
DEMO_SCRIPT.md     Client and technical demo outline
```

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
copy ..\.env.example .env       # then edit DATABASE_URL if needed
```

Start PostgreSQL (Docker is the simplest option):

```bash
docker compose up db -d
```

Then:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

## Docker instructions

```bash
docker compose up --build
```

This starts PostgreSQL (host port 5434), the API on port 8000, and the UI on port 8088. Host ports 5434 and 8088 avoid clashing with other local Postgres and HTTP services.

Populate historical data (required before the dashboard has numbers):

```bash
docker compose --profile import run --rm importer
```

The importer talks to Elexon, so it needs outbound HTTPS. A full January 2026 load typically takes a few minutes.

## Environment variables

See `.env.example`.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy URL for PostgreSQL |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `ELEXON_BASE_URL` | `https://data.elexon.co.uk/bmrs/api/v1` |
| `DECISION_CUTOFF_HOUR` / `DECISION_CUTOFF_MINUTE` | Configurable purchasing cutoff |
| `DECISION_CUTOFF_TIMEZONE` | Default `Europe/London` |
| `MAPE_MIN_ACTUAL_MW` | Actuals below this are excluded from MAPE |
| `VITE_API_BASE_URL` | Frontend API prefix, default `/api` |

## Historical data import

The assignment window is purchasing decisions in January 2026. WindScope imports:

- FUELHH WIND actuals for 1 January 2026 through 1 February 2026
- WINDFOR revisions published from 30 December 2025 through 1 February 2026

Commands:

```bash
# inside backend, with DATABASE_URL pointing at Postgres
python -m app.cli import-historical

# or via Compose
docker compose --profile import run --rm importer
```

The load is idempotent. Unique constraints prevent duplicate actuals and duplicate forecast revisions. Revisions are kept, not overwritten.

If Elexon is unavailable, the import fails with an error and the API continues to serve whatever was already stored. Missing observations are never filled with fabricated generation values.

## API documentation

FastAPI serves OpenAPI at `/docs`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Process and database health |
| GET | `/api/dashboard/summary` | KPIs, daily error, coverage |
| GET | `/api/generation/series` | Chart series |
| GET | `/api/generation/table` | Paginated period table |
| GET | `/api/generation/export` | CSV export |
| GET | `/api/forecasts/targets` | Hourly target timestamps |
| GET | `/api/forecasts/revisions` | Revisions for one target |
| GET | `/api/accuracy/metrics` | MAE, RMSE, bias, MAPE |
| GET | `/api/accuracy/daily` | Daily accuracy |
| GET | `/api/accuracy/distribution` | Histogram, hour-of-day, worst periods |
| GET | `/api/data/quality` | Coverage facts and methodology |

Query parameters: `from`, `to` (delivery dates, inclusive), `selection=decision_time|latest_before_delivery`, and `granularity=daily|hourly|half_hourly` where relevant.

Supported delivery dates: 2026-01-01 to 2026-02-01.

## Forecast selection methodology

This is the core business rule.

Each WINDFOR row has:

- `startTime` — the delivery hour being forecast
- `publishTime` — when that revision became available
- `generation` — forecast MW

**Default mode: latest available forecast at decision time**

1. Convert the delivery `startTime` to Europe/London.
2. Take the previous UK calendar day.
3. Build a cutoff at 09:50 on that day in Europe/London (configurable).
4. Keep revisions with `publishTime <= cutoff`.
5. Select the remaining revision with the latest `publishTime`.
6. If none remain, the period has no eligible forecast.

Forecasts published after the cutoff are excluded. That behaviour is covered by unit tests.

**Assumption, not a confirmed market rule:** 09:50 Europe/London is used because it matches Nord Pool N2EX GB day-ahead auction gate closure. It is a configurable proxy for “when the purchasing decision was made”, not an internal desk policy.

**Comparison mode:** `latest_before_delivery` uses the delivery `startTime` as the cutoff instead, so later intra-day revisions can be compared. The UI labels this separately so it is never confused with the decision-time forecast.

Duplicate `(start_time, publish_time)` rows are dropped before selection.

## Accuracy calculation methodology

Metrics use only timestamps that have both an actual and a selected eligible forecast. Missing values are not treated as zero.

| Metric | Formula |
| --- | --- |
| Error | Forecast − Actual |
| MAE | mean(\|Forecast − Actual\|) |
| RMSE | sqrt(mean((Forecast − Actual)²)) |
| Bias | mean(Forecast − Actual) |
| MAPE | mean(\|(Actual − Forecast) / Actual\|) × 100 |

MAPE excludes periods where `|Actual| < 1 MW` (configurable), including zeros. The API returns the valid sample count and the excluded count. Do not rely on MAPE alone.

**Resolution:** FUELHH is half-hourly average MW. WINDFOR is an hourly MW forecast. Accuracy compares one observation per UTC hour: the mean of the `:00` and `:30` actuals, matched to the selected hourly forecast. Both half-hours must exist; incomplete hours are dropped. The forecast is not copied onto both half-hours for MAE, RMSE, bias, MAPE, or coverage, because that would double-count each forecast.

Date filters are **inclusive UK delivery dates**. The purchasing decision date is the previous UK calendar day. Overview and Data Quality use the same `from`/`to` window for expected-hour counts, so a 1–31 January delivery filter yields 744 expected hours on both pages. Extending `to` to 1 February includes the delivery day for 31 January decisions (768 hours). Daily mean MW is the mean of those hourly MW values. Daily energy is `sum(hourly MW × 1 h)`.

## Testing instructions

```bash
cd backend
pytest

cd ../frontend
npm test
npm run build
```

Backend tests cover forecast cutoff logic, exclusion of future-published revisions, multiple revisions, duplicates, MAE, RMSE, bias, MAPE zero handling, missing observations, date boundaries, and an API integration fixture.

## Deployment instructions

The application is prepared for deployment. It has not been claimed as live unless a URL is added below after a real deploy.

**Frontend (Vercel)**

- Root directory: `frontend`
- Build command: `npm run build`
- Output: `dist`
- Environment: `VITE_API_BASE_URL` set to the public API origin, for example `https://windscope-api.onrender.com/api`

**Backend (Render or Heroku)**

- Root directory: `backend`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/health`
- Provision PostgreSQL and set `DATABASE_URL`
- Set `CORS_ORIGINS` to the Vercel URL
- Run `python -m app.cli import-historical` once against the production database

`render.yaml` and `backend/Procfile` are included. Serverless Vercel Python is a poor fit here because the API needs a persistent PostgreSQL connection pool and a one-off import job.

**Deployed application:** not deployed from this workspace.

## Known limitations

- FUELHH `WIND` outturn and WINDFOR NESO forecasts are related national wind series, but they are not guaranteed to cover an identical plant set.
- The 09:50 UK-time cutoff is an assumption.
- WINDFOR is hourly; actuals are half-hourly and are aggregated to hourly mean MW for scoring.
- The product is scoped to January 2026 decision dates plus 1 February delivery.
- Dashboard queries require a completed historical import. Empty KPIs mean “no matched data”, not zero generation.
- January 2026 is GMT, so UK local time equals UTC for this window.
