# Phase 2: Docker Stack — Airflow + PostgreSQL + dbt

## Overview

Phase 2 moves from a purely local setup to a fully **Dockerized** data engineering stack. Every service runs in an isolated container that can be started with a single command.

**Time to Complete:** 2–3 hours  
**Tech Stack:** Docker Compose · Apache Airflow 2.10.2 · PostgreSQL 15 · dbt 1.9

**Prerequisites:** Complete Phase 1 (DuckDB + Streamlit working locally)

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   Docker Network: de-network                 │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                  PostgreSQL :5432                      │  │
│  │      ┌────────────────┐  ┌──────────────────────┐     │  │
│  │      │   stocks DB    │  │     airflow DB       │     │  │
│  │      │  (your data)   │  │  (scheduler meta)    │     │  │
│  │      └────────────────┘  └──────────────────────┘     │  │
│  └────────────────────────────────────────────────────────┘  │
│           ▲                      ▲                            │
│           │                      │                            │
│  ┌────────┴───────┐    ┌────────┴──────────────────────┐    │
│  │   Streamlit    │    │         Airflow                │    │
│  │   :8501        │    │  ┌─────────────┐ ┌──────────┐ │    │
│  │  (Phase 1 UI)  │    │  │  scheduler  │ │webserver │ │    │
│  └────────────────┘    │  │  (runs DAGs)│ │  :8080   │ │    │
│                        │  └──────┬──────┘ └──────────┘ │    │
│                        └─────────┼──────────────────────┘    │
│                                  │ etl_prices_dag             │
│                        ┌─────────▼──────────────────────┐    │
│                        │  4-Task Pipeline                │    │
│                        │  1. download_prices (yfinance)  │    │
│                        │  2. store_to_duckdb             │    │
│                        │  3. push_to_postgres            │    │
│                        │  4. validate_postgres           │    │
│                        └────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## Services at a Glance

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| `postgres` | `de-bootcamp-postgres` | 5432 | PostgreSQL 15 (stocks + airflow DBs) |
| `airflow-init` | `de-bootcamp-airflow-init` | — | One-time DB migration + admin user |
| `airflow-scheduler` | `de-bootcamp-airflow-scheduler` | — | Runs DAGs on cron schedule |
| `airflow-webserver` | `de-bootcamp-airflow-webserver` | 8080 | Airflow UI |
| `streamlit` | `de-bootcamp-streamlit` | 8501 | Data app UI |
| `dbt` | `de-bootcamp-dbt` | — | dbt runner (on-demand via `docker-compose run`) |
| `ollama` | `de-bootcamp-ollama` | 11434 | Local LLM (Phase 5, `--profile phase5`) |

---

## One-Time Setup

> [!IMPORTANT]
> Run these steps only once after cloning the repository.

### Step 1 — Copy environment file

```bash
cp .env.example .env
```

No edits needed for local development — all defaults work.

### Step 2 — Create local data directory

```bash
mkdir -p data
```

### Step 3 — Start the full stack

```bash
docker-compose up -d
```

First run takes **3–5 minutes** to:
- Pull `apache/airflow:2.10.2` (~1.2 GB) and `postgres:15` images
- Run `airflow-init` to migrate the Airflow DB and create the admin user
- Start all services

### Step 4 — Verify all services are healthy

```bash
docker-compose ps
```

Expected output:
```
NAME                               STATUS           PORTS
de-bootcamp-airflow-init           Exit 0           ← Correct! One-time task done
de-bootcamp-airflow-scheduler      Up (healthy)
de-bootcamp-airflow-webserver      Up (healthy)     0.0.0.0:8080->8080/tcp
de-bootcamp-postgres               Up (healthy)     0.0.0.0:5432->5432/tcp
de-bootcamp-streamlit              Up               0.0.0.0:8501->8501/tcp
```

> [!NOTE]
> `airflow-init` showing `Exit 0` is **expected and correct**. It runs once and exits cleanly.

### Step 5 — Open the UIs

| App | URL | Credentials |
|-----|-----|-------------|
| **Streamlit** | http://localhost:8501 | — |
| **Airflow** | http://localhost:8080 | `admin` / `admin` |

---

## Airflow DAG: `etl_prices_dag`

### Pipeline Overview

The DAG runs **4 tasks in sequence** every day at **08:00 UTC**:

```
download_prices → store_to_duckdb → push_to_postgres → validate_postgres
```

| Task | What it does |
|------|-------------|
| `download_prices` | Downloads daily OHLCV from Yahoo Finance for all symbols in `config/symbols.toml` |
| `store_to_duckdb` | Upserts data into local DuckDB (conflict-safe — no duplicates) |
| `push_to_postgres` | Reads DuckDB → upserts into PostgreSQL `prices` table (skipped if `POSTGRES_URL` not set) |
| `validate_postgres` | Checks row counts; fails DAG if PostgreSQL is empty |

### Symbols configured

Defined in [`config/symbols.toml`](../config/symbols.toml):

```toml
[default]
symbols = ["AAPL", "MSFT", "ITC.NS", "LUPIN.NS", "GOOGL", "TSLA", "BTC-USD"]
```

### How to enable and trigger

**Via Airflow UI:**
1. Open http://localhost:8080 (Login: `admin` / `admin`)
2. Find `etl_prices_dag` → toggle **ON** to unpause the DAG.
3. Click **▶ Trigger DAG** to run immediately.

**Via CLI (End-to-End Test Flow):**

1. **Unpause the DAG** (must be done once, otherwise triggered runs will stay queued):
   ```bash
   docker-compose exec airflow-scheduler airflow dags unpause etl_prices_dag
   ```

2. **Trigger the DAG manually**:
   ```bash
   docker-compose exec airflow-scheduler airflow dags trigger etl_prices_dag
   ```

3. **Check DAG run status**:
   ```bash
   docker-compose exec airflow-scheduler airflow dags list-runs -d etl_prices_dag
   ```

4. **Monitor individual task states** in the latest run:
   ```bash
   # Replace the timestamp below with the execution_date shown by list-runs
   docker-compose exec airflow-scheduler airflow tasks states-for-dag-run etl_prices_dag manual__2026-06-02T17:26:43+00:00
   ```
   *Expected output: All tasks (`download_prices`, `store_to_duckdb`, `push_to_postgres`, `validate_postgres`) should show `success`.*

5. **Read execution logs** for a specific task (e.g. `download_prices`):
   ```bash
   # List log files inside the scheduler container
   docker-compose exec airflow-scheduler find /opt/airflow/logs -type f
   
   # View task log file directly
   docker-compose exec airflow-scheduler cat "/opt/airflow/logs/dag_id=etl_prices_dag/run_id=manual__2026-06-02T17:26:43+00:00/task_id=download_prices/attempt=1.log"
   ```

### Change the schedule

Edit [`airflow/dags/etl_prices_dag.py`](../airflow/dags/etl_prices_dag.py):

```python
schedule_interval="0 8 * * *",     # 08:00 UTC daily (current)
# schedule_interval="0 */4 * * *",   # Every 4 hours
# schedule_interval="@hourly",
# schedule_interval="@daily",
```

Then restart the scheduler:
```bash
docker-compose restart airflow-scheduler
```

---

## PostgreSQL Verification

Verify that data was successfully synced from DuckDB to PostgreSQL after the DAG run finishes:

```bash
# Connect to stocks database in the postgres container
docker-compose exec postgres psql -U postgres -d stocks

# Inside psql:
\dt                                              -- list tables (should show prices)
SELECT symbol, COUNT(*) FROM prices GROUP BY symbol;   -- row counts per symbol
SELECT * FROM prices ORDER BY timestamp DESC LIMIT 5;  -- view latest ingested rows
\q                                               -- exit psql
```

Expected output for row counts per symbol:
```
  symbol  | count 
----------+-------
 AAPL     |    21
 MSFT     |    21
 GOOGL    |     5
 LUPIN.NS |    22
 BTC-USD  |     5
 ITC.NS   |    22
 TSLA     |     5
(7 rows)
```
*(Note: DuckDB stores full historical data while Airflow pushes the last 30 days of data to PostgreSQL during daily syncs).*

---

## Data Flow: DuckDB ↔ PostgreSQL

```
yfinance API
    ↓
load_prices_daily()  [app/core/etl/prices.py]
    ↓
DuckDB (data/app.duckdb)  ← local cache, persists between runs
    ↓
pg_loader.fetch_from_duckdb()  [scripts/pg_loader.py]
    ↓
PostgreSQL (stocks.public.prices)  ← persistent warehouse
    ↓
Streamlit Data Explorer  ← UI visualization + CSV export
```

### Manual push (without Airflow)

```bash
# Push all symbols immediately
uv run python -m scripts.schedule_pg_sync --now --all

# Push specific symbols
uv run python -m scripts.schedule_pg_sync --now --symbols AAPL,MSFT,ITC.NS,LUPIN.NS
```

---

## dbt (Phase 3 preview)

dbt runs against PostgreSQL inside Docker:

```bash
# Test connection
docker-compose run --rm dbt debug --target docker

# Run all models
docker-compose run --rm dbt run --target docker

# Run tests
docker-compose run --rm dbt test --target docker

# Generate docs
docker-compose run --rm dbt docs generate --target docker
```

> [!TIP]
> The `dbt` service is in the `dbt` profile — it only starts when explicitly called with `docker-compose run`.

---

## Daily Operations

```bash
# Start all services (e.g. after machine restart)
docker-compose up -d

# Stop all services (data volumes are preserved)
docker-compose down

# View logs for a service
docker-compose logs -f airflow-scheduler
docker-compose logs -f airflow-webserver
docker-compose logs -f streamlit
docker-compose logs -f postgres

# Restart a single service
docker-compose restart airflow-scheduler

# Wipe everything including data (fresh start)
docker-compose down -v
```

---

## Troubleshooting

### `airflow-init` fails with `ModuleNotFoundError: No module named 'airflow.__main__'`

Caused by `pip install` overwriting Airflow's pinned `protobuf`. Fixed in the current setup by using `docker/airflow-requirements.txt` which avoids conflicting packages.

```bash
# Verify airflow-init completed cleanly
docker inspect --format='{{.State.ExitCode}}' de-bootcamp-airflow-init
# Should output: 0
```

### DAG not appearing in Airflow UI

```bash
# Check for syntax errors
docker-compose exec airflow-scheduler python -c "
import sys; sys.path.insert(0, '/opt/airflow')
import importlib; importlib.import_module('airflow.dags.etl_prices_dag')
print('DAG syntax OK')
"
```

### PostgreSQL connection refused

```bash
docker-compose ps postgres          # Check it's healthy
docker-compose restart postgres
sleep 15
docker-compose restart airflow-scheduler airflow-webserver
```

### Streamlit shows "No data in DuckDB"

The DuckDB file is stored in the `duckdb_data` Docker volume. To pre-populate from your local DuckDB:

```bash
# Copy your local DuckDB into the Docker volume
docker run --rm -v $(pwd)/data:/src \
  -v de-bootcamp-summer2026_duckdb_data:/dst \
  alpine cp /src/app.duckdb /dst/app.duckdb
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_URL` | `postgresql+psycopg2://postgres:postgres@postgres:5432/stocks` | Stock data DB connection |
| `DUCKDB_PATH` | `data/app.duckdb` | Local DuckDB file path |
| `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` | `postgresql+psycopg2://...@postgres:5432/airflow` | Airflow metadata DB |
| `AIRFLOW__CORE__EXECUTOR` | `LocalExecutor` | Task execution mode |
| `AIRFLOW__CORE__FERNET_KEY` | (set in docker/airflow.env) | Encryption key for connections |

---

## Next Steps After Phase 2

Once you're comfortable with:
- Starting/stopping the Docker stack
- Monitoring DAG runs in the Airflow UI
- Verifying data flows from yfinance → DuckDB → PostgreSQL

You're ready for **Phase 3: dbt Data Transformations**!

See [PHASE_3_DBT.md](PHASE_3_DBT.md)
