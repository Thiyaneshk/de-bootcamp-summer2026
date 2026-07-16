# 📊 Antigravity Session Status

> **Agent:** Antigravity  
> **Last Updated:** 16 July 2026 10:38 BRT  
> **Repo:** `de-bootcamp-summer2026`  
> **Status file location:** `antigravity_status.md` (project root)

---

## 🏗️ Current Architecture

```
yfinance API
    ↓
DuckDB (local cache: data/app.duckdb)  ← Phase 1 (dev only)
    ↓
PostgreSQL (warehouse: stocks DB)       ← Phase 2 (production)
    ↓
dbt transformations                     ← Phase 3
    ↓
┌─────────────────────────────────────────┐
│ Streamlit UI (8 pages)                  │ ← Phase 1/4/5/10
│  • Home Dashboard                        │
│  • Stock Overview (candlestick)          │
│  • Data Explorer (DuckDB)                │
│  • Technical Indicators (PG)             │
│  • Analytics & Insights (PG)             │
│  • AI Assistant Chat (Ollama)            │
│  • Ticker Registry (Phase 10) ← NEW     │
│  • Admin Panel                           │
└─────────────────────────────────────────┘
```

**Instrument Registry (Phase 10):**
```
registry.instruments         ← master list of all tracked symbols
registry.index_constituents  ← S&P 500 / NASDAQ-100 / Nifty 50 memberships
registry.ingestion_log       ← audit trail of ETL runs
```

**Airflow DAGs:**
```
resolve_index_membership  (weekly Sun 00:00 UTC)
  → Scrape S&P 500, NASDAQ-100, Nifty 50 from Wikipedia
  → Auto-register ~650 instruments

etl_daily_prices  (daily 08:00 UTC)
  → Query active instruments from registry
  → Dynamic task mapping: one task per ticker (expand)
  → yfinance → DuckDB → PostgreSQL → ingestion_log
  → dbt run
```

**Key config:**
- `DB_BACKEND` env var: `duckdb` | `postgres` | `snowflake`
- Symbols: DB registry (primary) / `config/symbols.toml` (legacy fallback)
- Seed data: `data/ticker_registry_seed.csv` (193 instruments: IN/CA/US)
- dbt profiles: `dbt/profiles.yml` (dev=duckdb, prod=postgres, snowflake)

---

## ✅ Completed Work

### Session 1 — 14 July 2026
- PR cherry-pick (Phase 8 Databricks + Phase 9 Terraform)
- Documentation updates (README.md, SETUP_COMMANDS.md → 7 phases)
- UI overhaul (11 fixes across all pages)
- All 11 tests passing, benchmark verified

### Session 2 — 14–16 July 2026 (user-driven)
- Phase 10: Ticker Registry tables + CRUD module (`app/db/registry.py`)
- Airflow ETL DAG rewrite with dynamic task mapping (`expand()`)
- Index membership DAG stub
- Seed script + CSV (193 instruments for IN/CA/US markets)
- Registry tests (2 new) + seed test (1 new) → 14 total tests

### Session 3 — 16 July 2026 (Antigravity continuation)
- Cleaned 14 leftover files (`.orig`, `.rej`, `.patch`, temp scripts)
- **Rewrote Ticker Registry UI** — form-based add, DataFrame display, toggle/enable-all, seed button, read-only ingestion log
- **Rewrote `resolve_index_membership_dag.py`** — real Wikipedia scraping for S&P 500 (500 stocks), NASDAQ-100 (100 stocks), Nifty 50 (50 stocks)
- Updated Home Dashboard — Phase 10 tasks expanded, Quick Links added
- All 14 tests passing ✅

---

## 📁 Key Files Reference

| Purpose | File |
|---------|------|
| App entry point | `app/main.py` |
| Config | `app/config.py`, `config/symbols.toml` |
| DB connections | `app/db/connection.py`, `app/db/__init__.py` |
| **Ticker Registry** | `app/db/registry.py` |
| **Registry UI** | `app/views/page_07_ticker_registry.py` |
| **Seed script** | `scripts/seed_registry.py` |
| **Seed data** | `data/ticker_registry_seed.csv` |
| ETL prices | `app/core/etl/prices.py` |
| Data refresh | `scripts/refresh_data.py` |
| Redis cache | `app/core/cache/redis_cache.py` |
| RAG chat engine | `app/core/rag/chat_engine.py` |
| **ETL DAG (dynamic)** | `airflow/dags/etl_prices_dag.py` |
| **Index membership DAG** | `airflow/dags/resolve_index_membership_dag.py` |
| dbt project | `dbt/dbt_project.yml`, `dbt/profiles.yml` |
| Tests | `tests/`, `run_tests.py`, `test_benchmark.py` |
| **This file** | `antigravity_status.md` |

---

## 🔮 Future Roadmap

### Phase 11: Databricks + Spark
- Deferred — data volume too small for Spark currently
- Will add when ML model training phase begins
- Path: Databricks Community → dbt-databricks → PySpark ETL → Delta Lake → MLflow

### Other Ideas
- InfluxDB for real-time tick data (sub-second) — not needed for daily OHLCV
- Kafka — Airflow dynamic tasks serve same purpose for batch

---

## 🔧 How to Resume

When starting a new session, point Antigravity to this file:
```
Review antigravity_status.md for context on what's been done and what's next.
```
