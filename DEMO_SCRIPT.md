# WindScope demo script

Two sections, ten minutes total. Use the running app with imported January 2026 Elexon data. Do not quote numbers that are not on screen.

## Part 1 — Client presentation (maximum 5 minutes)

### 1. Client problem (45 seconds)

Purchasing teams buy GB power in the day-ahead market. Wind output moves the residual position they have to buy. The question is not “what did the latest forecast say after the fact?” It is “what wind did we think we would get when we still had time to buy?”

### 2. Product overview (30 seconds)

WindScope is a UK wind forecast analytics product. It uses Elexon FUELHH WIND actuals and WINDFOR forecast revisions only. Open Overview. Point to the date range (January 2026 delivery) and the selection control defaulting to **Decision-time forecast**.

### 3. Dashboard demonstration (90 seconds)

Walk the KPI row: average actual, average forecast, MAE, RMSE, bias, coverage. Open the main chart and switch Daily / Half-hourly so it is clear that daily values are mean MW over equal settlement periods, not a hidden total.

Show daily MAE and the worst-error days. State that gaps are missing observations, not zeros.

### 4. Forecast accuracy insights (45 seconds)

Open Forecast Accuracy. Read MAE, RMSE, and bias from the cards. Mention MAPE only with its valid sample count and the exclusion of near-zero actuals. Point at over- vs under-forecast counts and the hour-of-day MAE chart.

### 5. Decision-time forecast selection (60 seconds)

Open Forecast Explorer. Pick a delivery hour. Show the revision table: older publishes, the highlighted decision forecast, and later publishes marked **No — after cutoff**. Switch the header to **Latest before delivery** and show that a later revision can appear in that comparison mode without changing what was available at 09:50 the day before.

State the cutoff assumption clearly: 09:50 Europe/London, aligned with N2EX gate closure, configurable, not a confirmed internal trading rule.

### 6. Business value and limitations (30 seconds)

Value: the desk can see whether day-ahead wind error is bias or scatter, and which days would have been most expensive to get wrong.

Limitations: FUELHH WIND and WINDFOR are related but not identical plant sets; WINDFOR is hourly; the cutoff is an assumption; the product does not price the error.

## Part 2 — Technical review (maximum 5 minutes)

### 1. System architecture (40 seconds)

Monorepo: React/Vite SPA, FastAPI, PostgreSQL. Docker Compose runs all three. Dashboard reads cached imports. Elexon is used only by `python -m app.cli import-historical`.

### 2. Database design (30 seconds)

`wind_actuals` unique on `start_time`. `wind_forecasts` unique on `(start_time, publish_time)` so revisions are retained. `import_runs` records load status. Alembic migration `001_initial_schema` plus `create_all` on startup for local bring-up.

### 3. Elexon integration (40 seconds)

Verified live:

- `GET /datasets/FUELHH/stream?settlementDateFrom=&settlementDateTo=&fuelType=WIND`
- `GET /datasets/WINDFOR/stream?publishDateTimeFrom=&publishDateTimeTo=`

JSON arrays. FUELHH filtered to `fuelType = WIND`. Chunked fetches, retries on 429/5xx, idempotent upserts.

### 4. Forecast selection algorithm (50 seconds)

For each hourly target: cutoff = previous UK calendar day at 09:50 London. Eligible if `publish_time <= cutoff`. Take max `publish_time`. Tests prove a 10:30 revision is excluded when 08:30 is selected.

Accuracy uses hourly mean actual MW (both :00 and :30 must exist) versus the selected hourly forecast. The forecast is not copied onto both half-hours for scoring.

### 5. Backend analytics (30 seconds)

Pandas/NumPy for matching and metrics. MAE / RMSE / bias on matched hours only. MAPE drops `|actual| < 1 MW`. Daily energy is `sum(hourly MW × 1 h)`.

### 6. Frontend architecture (30 seconds)

React Router pages, TanStack Query, Axios client, Recharts, shared date/selection query params, skeleton and error states, CSV download from `/api/generation/export`.

### 7. Testing and Docker (20 seconds)

`pytest` in `backend/` (selection, metrics, API fixture). `npm test` and `npm run build` in `frontend/`. `docker compose up --build` then `docker compose --profile import run --rm importer`.

### 8. Tradeoffs and limitations (20 seconds)

Postgres rather than SQLite for deployment. Import is offline, not per request. 09:50 cutoff is documented as an assumption. No prices or weather, by design.
