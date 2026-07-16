# Step-by-Step Learning and Testing Guide

This guide is meant to be used like a mini syllabus for the project. Follow it in order if you want to learn the app from the ground up, one layer at a time.

The goal is to help you:
- understand how the app works,
- test each feature yourself,
- learn the technologies behind it,
- and know where to look when something breaks.

---

## 1. First, understand what this repository is

This project is a hands-on learning app for stock data engineering. It brings together:
- Streamlit for the UI,
- yfinance for stock data,
- DuckDB and PostgreSQL for storage,
- Airflow for orchestration,
- dbt for transformations,
- Ollama + RAG for AI chat,
- Redis for caching,
- and a registry layer for managing symbols.

### Main entry points
- App UI: [app/main.py](../app/main.py)
- Stock overview page: [app/views/page_02_stock_overview.py](../app/views/page_02_stock_overview.py)
- AI chat page: [app/views/page_06_assistant_chat.py](../app/views/page_06_assistant_chat.py)
- Ticker registry page: [app/views/page_07_ticker_registry.py](../app/views/page_07_ticker_registry.py)
- ETL logic: [app/core/etl/prices.py](../app/core/etl/prices.py)
- Database abstraction: [app/db/connection.py](../app/db/connection.py)
- Airflow DAG: [airflow/dags/etl_prices_dag.py](../airflow/dags/etl_prices_dag.py)
- RAG chat engine: [app/core/rag/chat_engine.py](../app/core/rag/chat_engine.py)
- Redis cache wrapper: [app/core/cache/redis_cache.py](../app/core/cache/redis_cache.py)
- Tests: [tests](../tests)

---

## 2. Prepare your environment

### Step 2.1: Check prerequisites
Make sure you have:
- Python 3.11+
- uv installed
- Docker and Docker Compose available
- Git

### Step 2.2: Install dependencies
Start with the app and dev tools:

```bash
uv sync --extra phase1 --extra dev
```

If you want to test the full stack later, install more extras:

```bash
uv sync --extra phase1 --extra phase2 --extra phase3 --extra phase5 --extra phase6 --extra phase7 --extra dev
```

### Step 2.3: Create your environment file
If a .env file does not exist yet:

```bash
cp .env.example .env
```

Then open it and verify the values, especially if you plan to use PostgreSQL or Ollama.

### Step 2.4: Verify the environment
Run these checks:

```bash
uv --version
python3 --version
```

Expected result:
- uv is available,
- Python version is 3.11 or newer.

---

## 3. Run the Streamlit app and learn the UI

### Step 3.1: Start the app
Run:

```bash
uv run streamlit run app/main.py
```

Open:
- http://localhost:8501

### Step 3.2: Explore each page in the sidebar
The app has multiple pages:
- Home
- Stock Overview
- Data Explorer
- Indicators
- Analysis
- Assistant Chat
- Ticker Registry
- Admin

### What to learn from each page
- Home: see the overall app layout and branding.
- Stock Overview: test how market data is fetched and displayed.
- Data Explorer: inspect how data is presented to the user.
- Indicators: learn how technical indicators are conceptualized.
- Analysis: review the analytical workflow.
- Assistant Chat: test AI-powered questions over data.
- Ticker Registry: **(Phase 10)** Learn how active symbols and index constituents are managed in a database.
- Admin: inspect app-level control points.

### Step 3.3: Try the Stock Overview page
Use a symbol like AAPL or MSFT and click Load Data.

What you should observe:
- the app fetches market data,
- charts appear,
- summary metrics are shown,
- and a data table is presented.

This page is a good place to start learning the UI + ETL connection.

---

## 4. Test the ETL layer directly from Python

The ETL logic is implemented in [app/core/etl/prices.py](../app/core/etl/prices.py).

### Step 4.1: Load daily data
Run:

```bash
uv run python -c "from app.core.etl.prices import load_prices_daily; df = load_prices_daily('AAPL', period='1mo'); print(df.head()); print('rows=', len(df))"
```

### Step 4.2: Load 5-minute data
Run:

```bash
uv run python -c "from app.core.etl.prices import load_prices_5m; df = load_prices_5m('AAPL', start_date='2026-05-13'); print(df.head()); print('rows=', len(df))"
```

### Step 4.3: Learn what is happening
Pay attention to:
- how yfinance is called,
- how the DataFrame is normalized,
- and how the result is returned to the UI.

### Step 4.4: Try a second symbol
Replace AAPL with MSFT, GOOGL, or BTC-USD and see how the behavior changes.

---

## 5. Test local data storage with DuckDB

The database abstraction is in [app/db/connection.py](../app/db/connection.py).

### Step 5.1: Open the local DuckDB database
Run:

```bash
uv run python -c "import duckdb; conn = duckdb.connect('data/app.duckdb'); print(conn.execute('SHOW TABLES').fetchall()); conn.close()"
```

### Step 5.2: Create a small test table
Run:

```bash
uv run python -c "import duckdb; conn = duckdb.connect('data/app.duckdb'); conn.execute('CREATE TABLE IF NOT EXISTS demo_test (id INT, label VARCHAR)'); conn.execute('INSERT INTO demo_test VALUES (1, \"hello\")'); print(conn.execute('SELECT * FROM demo_test').fetchall()); conn.close()"
```

### Step 5.3: Learn the difference between DuckDB and PostgreSQL
The repo supports both. DuckDB is the lightweight local option for development. PostgreSQL is used when POSTGRES_URL is set.

Useful file:
- [app/db/connection.py](../app/db/connection.py)

---

## 6. Test the database layer and registry features

The registry module is in [app/db/registry.py](../app/db/registry.py).

### Step 6.1: Open the Ticker Registry page
Start the app and go to the Ticker Registry page.

### Step 6.2: Add an instrument
Try adding:
- symbol: AAPL
- name: Apple Inc.
- type: stock
- exchange: NASDAQ

Then click Save instrument.

### Step 6.3: Seed sample index membership
Use the "Seed from CSV" button in the sidebar.
This will load around 193 instruments across IN, CA, and US markets (including index definitions).

### Step 6.4: Explore Index Constituents
Go to the "Index Membership" tab. You will see active symbols. The pipeline auto-discovers S&P 500, NASDAQ-100, and Nifty 50 constituents dynamically via the `resolve_index_membership` Airflow DAG.

### Step 6.5: Learn what is being stored
The registry stores:
- instruments (active vs inactive),
- index memberships (weights, dates),
- ingestion history (success, skipped, failed).

This database registry fully replaces the old `config/symbols.toml` file, bringing the app closer to a production-grade orchestration system.

---

## 7. Test the manual refresh script

The refresh script is in [scripts/refresh_data.py](../scripts/refresh_data.py).

### Step 7.1: Refresh one symbol
Run:

```bash
uv run python scripts/refresh_data.py --symbols AAPL
```

### Step 7.2: Refresh all configured symbols
Run:

```bash
uv run python scripts/refresh_data.py --all
```

### What to observe
- the script loads fresh data,
- inserts or updates rows,
- and uses the configured symbols from [config/symbols.toml](../config/symbols.toml).

---

## 8. Learn the Airflow workflow

The DAG is in [airflow/dags/etl_prices_dag.py](../airflow/dags/etl_prices_dag.py).

### Step 8.1: Start PostgreSQL
Run:

```bash
docker compose up -d postgres
```

### Step 8.2: Set the PostgreSQL URL in your environment
Example:

```bash
export POSTGRES_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/stocks"
```

### Step 8.3: Initialize the database schema
Run:

```bash
uv run python scripts/init_db.py
```

### Step 8.4: Start Airflow services
Run:

```bash
docker compose up -d airflow-init airflow-scheduler airflow-webserver
```

Then visit:
- http://localhost:8080

### Step 8.5: Open the DAG in Airflow UI
Look for the DAG named etl_prices_dag.

### Step 8.6: Trigger it manually
Click Run or Trigger DAG.

### What you should learn
- Airflow orchestrates tasks.
- In Phase 10, the daily DAG (`etl_prices_dag.py`) queries the active symbols from your database registry.
- It uses **Dynamic Task Mapping** (`.expand()`) to fan-out and download each ticker in parallel!
- The weekly DAG (`resolve_index_membership_dag.py`) automatically scrapes Wikipedia for index constituents and updates your registry.

---

## 9. Learn the dbt transformation layer

The dbt project lives in [dbt](../dbt).

### Step 9.1: Inspect the dbt structure
Look at:
- [dbt/dbt_project.yml](../dbt/dbt_project.yml)
- [dbt/models](../dbt/models)
- [dbt/profiles.yml](../dbt/profiles.yml)

### Step 9.2: Run dbt models
If your environment is ready, try:

```bash
docker compose run --rm dbt run --target prod
```

### Step 9.3: Run dbt tests
Run:

```bash
docker compose run --rm dbt test --target prod
```

### What to learn
- staging models clean the source data,
- marts are the analytics-ready tables,
- and dbt adds a layer of testing and transformation.

---

## 10. Test the AI assistant and RAG workflow

The chat logic is implemented in [app/core/rag/chat_engine.py](../app/core/rag/chat_engine.py), and the UI is in [app/views/page_06_assistant_chat.py](../app/views/page_06_assistant_chat.py).

### Step 10.1: Install or start Ollama
If you want the full experience, run:

```bash
bash scripts/init_ollama.sh
```

You may also need to pull a model:

```bash
ollama pull gemma4:latest
```

### Step 10.2: Start the app
Run the Streamlit app again and open the Assistant Chat page.

### Step 10.3: Ask sample questions
Try prompts like:
- What was the latest close price of AAPL?
- Compare MSFT and GOOGL over the last few days.
- Which stock has the highest volatility?

### What to learn
- the assistant uses a retrieval step,
- it pulls database context before answering,
- and it is designed to respond based on stored data rather than raw internet knowledge.

> If Ollama is not available, the page should still load and explain the missing setup gracefully.

---

## 11. Test Redis-based caching

The caching wrapper is in [app/core/cache/redis_cache.py](../app/core/cache/redis_cache.py).

### Step 11.1: Start Redis
Run:

```bash
docker compose up -d redis
```

### Step 11.2: Make repeated ETL calls
Run the same price-loading command twice:

```bash
uv run python -c "from app.core.etl.prices import load_prices_daily; df = load_prices_daily('AAPL', period='1mo'); print(len(df))"
```

### What to learn
- the app uses a Redis cache wrapper around ETL functions,
- repeated calls can reuse cached results,
- and if Redis is unavailable, the code falls back safely.

---

## 12. Run the automated tests

The test suite is in [tests](../tests).

### Step 12.1: Run smoke tests first
```bash
uv run python run_tests.py
```
This runs the full suite (14 tests) via `pytest` efficiently.

### What to learn
- tests cover import paths,
- configuration loading,
- database access (with local DuckDB roundtrips),
- RAG chat module compatibility,
- and registry seed validation.

If a test fails, read the relevant module and the test file together before changing anything.

---

## 13. Learn the repo by feature, not just by file

A simple mental model for the project:
- [app/views](../app/views): user experience and pages
- [app/core/etl](../app/core/etl): fetching data from yfinance
- [app/db](../app/db): storage and registry logic
- [airflow/dags](../airflow/dags): scheduled orchestration
- [dbt](../dbt): transformations and modeling
- [app/core/rag](../app/core/rag): AI assistant and retrieval
- [config/symbols.toml](../config/symbols.toml): symbols to track
- [tests](../tests): confidence and regression checks

---

## 14. Suggested learning order for beginners

If you want a simple path, follow this sequence:
1. Run the Streamlit app.
2. Test the ETL helper functions.
3. Explore the local DuckDB database.
4. Open the Ticker Registry page.
5. Try the manual refresh script.
6. Learn the Airflow DAG.
7. Run dbt.
8. Try the AI chat page.
9. Run tests.

---

## 15. Good checkpoints to know you are progressing

You are making progress when you can:
- load stock data from the UI,
- run ETL functions from Python,
- inspect data in DuckDB or PostgreSQL,
- trigger the Airflow DAG,
- see dbt output models,
- ask the assistant questions and receive context-backed answers,
- and run tests without major import errors.

---

## 16. Where to go next

After finishing this guide, the next best step is to open the phase-specific docs in [docs](../docs):
- [docs/PHASE_1_STREAMLIT.md](PHASE_1_STREAMLIT.md)
- [docs/PHASE_2_AIRFLOW_POSTGRES.md](PHASE_2_AIRFLOW_POSTGRES.md)
- [docs/PHASE_3_DBT.md](PHASE_3_DBT.md)
- [docs/PHASE_4_ANALYTICS.md](PHASE_4_ANALYTICS.md)
- [docs/PHASE_5_LLM_RAG.md](PHASE_5_LLM_RAG.md)
- [docs/PHASE_6_REDIS.md](PHASE_6_REDIS.md)
- [docs/PHASE_7_SNOWFLAKE.md](PHASE_7_SNOWFLAKE.md)
- [docs/PHASE_10_REGISTRY.md](PHASE_10_REGISTRY.md)

That is the best way to connect the high-level app flow to the deeper technical concepts.
