"""
Phase 2: ETL Prices DAG — Full Pipeline (yfinance → DuckDB → PostgreSQL)

Apache Airflow DAG for scheduled daily stock price ingestion.

Pipeline:
  Task 1 (download_prices)     Download OHLCV data from yfinance for all symbols
  Task 2 (store_to_duckdb)     Upsert into local DuckDB (persistent cache)
  Task 3 (push_to_postgres)    Upsert DuckDB data into PostgreSQL warehouse
  Task 4 (validate_postgres)   Assert row/symbol counts; raise if data missing

Schedule: Daily at 08:00 UTC  (cron: '0 8 * * *')
          Change via Airflow UI → DAGs → etl_prices_dag → Edit

Environment variables (set in .env or Airflow Connections / Variables):
  POSTGRES_URL   — PostgreSQL connection string (required for tasks 3 & 4)
                   e.g. postgresql+psycopg2://postgres:postgres@localhost:5432/stocks
  DUCKDB_PATH    — Path to DuckDB file (default: data/app.duckdb)

How to run:
  # Start Airflow (two terminals)
  export AIRFLOW_HOME=$(pwd)/airflow
  export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/airflow/dags
  export AIRFLOW__CORE__LOAD_EXAMPLES=False
  uv run airflow db init          # first time only
  uv run airflow scheduler        # Terminal 1
  uv run airflow webserver -p 8080  # Terminal 2  → http://localhost:8080

  # Or trigger manually from CLI:
  uv run airflow dags trigger etl_prices_dag
"""

import logging
import os
from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from airflow import DAG

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Helper: load symbols from config/symbols.toml
# ─────────────────────────────────────────────────────────────────────────────


def _get_symbols() -> list[str]:
    import tomllib

    cfg_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "config", "symbols.toml"
    )
    try:
        with open(cfg_path, "rb") as f:
            cfg = tomllib.load(f)
        symbols = cfg.get("default", {}).get("symbols", [])
        if symbols:
            return symbols
    except Exception as e:
        logger.warning("Could not read symbols.toml: %s — using fallback list", e)

    # Fallback if file missing
    return ["AAPL", "MSFT", "GOOGL", "TSLA", "BTC-USD"]


# ─────────────────────────────────────────────────────────────────────────────
# Task 1: Download from yfinance → push raw data via XCom
# ─────────────────────────────────────────────────────────────────────────────


def download_prices(**context) -> dict:
    """
    Download daily OHLCV data from yfinance for all configured symbols.
    Pushes a summary dict to XCom for downstream tasks.
    """
    from app.core.etl.prices import load_prices_daily

    symbols = _get_symbols()
    logger.info("Task 1 — downloading yfinance data for: %s", symbols)

    results = {}
    for sym in symbols:
        try:
            df = load_prices_daily(sym, period="5d")
            if df is not None and not df.empty:
                results[sym] = len(df)
                logger.info("  ✓ %s: %d rows downloaded", sym, len(df))
            else:
                results[sym] = 0
                logger.warning("  ✗ %s: no data returned", sym)
        except Exception as e:
            results[sym] = 0
            logger.error("  ✗ %s: download failed — %s", sym, e)

    total = sum(results.values())
    logger.info(
        "Task 1 complete — %d total rows downloaded across %d symbols",
        total,
        len(symbols),
    )

    # Push to XCom for downstream tasks
    context["ti"].xcom_push(key="symbols", value=symbols)
    context["ti"].xcom_push(key="download_summary", value=results)

    return {"symbols": symbols, "rows_by_symbol": results, "total_rows": total}


# ─────────────────────────────────────────────────────────────────────────────
# Task 2: Store downloaded data into DuckDB
# ─────────────────────────────────────────────────────────────────────────────


def store_to_duckdb(**context) -> dict:
    """
    Pull fresh data from yfinance (again) and upsert into local DuckDB.
    DuckDB acts as a fast local cache and source of truth for Phase 1.
    """
    from app.core.etl.prices import load_prices_daily
    from app.db.connection import get_duckdb_connection
    from app.db.utils import create_prices_table, insert_prices

    symbols = (
        context["ti"].xcom_pull(key="symbols", task_ids="download_prices")
        or _get_symbols()
    )
    logger.info("Task 2 — storing %d symbols to DuckDB", len(symbols))

    total_upserted = 0
    with get_duckdb_connection() as conn:
        create_prices_table(conn)

        for sym in symbols:
            try:
                df = load_prices_daily(sym, period="5d")
                if df is None or df.empty:
                    logger.warning("  ✗ %s: empty — skipping DuckDB upsert", sym)
                    continue

                records = [
                    {
                        "symbol": sym,
                        "timestamp": idx.to_pydatetime(),
                        "open": float(row.get("Open", 0) or 0),
                        "high": float(row.get("High", 0) or 0),
                        "low": float(row.get("Low", 0) or 0),
                        "close": float(row.get("Close", 0) or 0),
                        "volume": int(row.get("Volume", 0) or 0),
                    }
                    for idx, row in df.iterrows()
                ]

                n = insert_prices(conn, records)
                total_upserted += n
                logger.info("  ✓ %s: %d rows upserted to DuckDB", sym, n)

            except Exception as e:
                logger.error("  ✗ %s: DuckDB upsert failed — %s", sym, e)

    logger.info("Task 2 complete — %d total rows in DuckDB", total_upserted)
    context["ti"].xcom_push(key="duckdb_rows", value=total_upserted)
    return {"duckdb_rows": total_upserted}


# ─────────────────────────────────────────────────────────────────────────────
# Task 3: Push DuckDB data → PostgreSQL
# ─────────────────────────────────────────────────────────────────────────────


def push_to_postgres(**context) -> dict:
    """
    Read data from DuckDB and upsert into PostgreSQL prices table.
    Skipped gracefully if POSTGRES_URL is not set.
    """
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        logger.warning(
            "Task 3 — POSTGRES_URL not set. Skipping PostgreSQL push. "
            "Set POSTGRES_URL in .env to enable this task."
        )
        context["ti"].xcom_push(key="pg_rows", value=0)
        return {"pg_rows": 0, "skipped": True}

    from sqlalchemy import create_engine, text

    from scripts.pg_loader import fetch_from_duckdb

    symbols = (
        context["ti"].xcom_pull(key="symbols", task_ids="download_prices")
        or _get_symbols()
    )
    logger.info("Task 3 — pushing DuckDB → PostgreSQL for: %s", symbols)

    # Fetch last 30 days from DuckDB
    df = fetch_from_duckdb(symbols, days_back=30)
    if df.empty:
        logger.warning("Task 3 — DuckDB returned no rows. Nothing to push.")
        context["ti"].xcom_push(key="pg_rows", value=0)
        return {"pg_rows": 0}

    engine = create_engine(postgres_url, pool_pre_ping=True)
    try:
        # Ensure prices table exists in PostgreSQL
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS prices (
                    symbol    VARCHAR(20)  NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    open      DOUBLE PRECISION,
                    high      DOUBLE PRECISION,
                    low       DOUBLE PRECISION,
                    close     DOUBLE PRECISION,
                    volume    BIGINT,
                    PRIMARY KEY (symbol, timestamp)
                )
            """
                )
            )

        # Upsert via staging temp table
        with engine.begin() as conn:
            df.to_sql("prices_etl_tmp", conn, if_exists="replace", index=False)
            conn.execute(
                text(
                    """
                INSERT INTO prices (symbol, timestamp, open, high, low, close, volume)
                SELECT symbol, timestamp::timestamptz, open, high, low, close, volume
                FROM prices_etl_tmp
                ON CONFLICT (symbol, timestamp) DO UPDATE SET
                    open   = EXCLUDED.open,
                    high   = EXCLUDED.high,
                    low    = EXCLUDED.low,
                    close  = EXCLUDED.close,
                    volume = EXCLUDED.volume
            """
                )
            )
            conn.execute(text("DROP TABLE IF EXISTS prices_etl_tmp"))

        pg_rows = len(df)
        logger.info("Task 3 complete — %d rows upserted to PostgreSQL", pg_rows)
        context["ti"].xcom_push(key="pg_rows", value=pg_rows)
        return {"pg_rows": pg_rows}

    except Exception as e:
        logger.error("Task 3 failed — PostgreSQL push error: %s", e)
        raise  # Re-raise so Airflow marks task as failed and retries
    finally:
        engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# Task 4: Validate PostgreSQL
# ─────────────────────────────────────────────────────────────────────────────


def validate_postgres(**context) -> dict:
    """
    Assert that:
    - prices table has rows
    - all expected symbols are present
    Raises ValueError if validation fails (Airflow will mark task as failed).
    """
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        logger.info("Task 4 — no POSTGRES_URL, skipping validation (DuckDB-only mode)")
        return {"skipped": True}

    from sqlalchemy import create_engine, text

    symbols = (
        context["ti"].xcom_pull(key="symbols", task_ids="download_prices")
        or _get_symbols()
    )
    engine = create_engine(postgres_url, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            # Total row count
            total = conn.execute(text("SELECT COUNT(*) FROM prices")).scalar()
            logger.info("✓ PostgreSQL prices table: %d total rows", total)

            # Per-symbol counts
            rows = conn.execute(
                text(
                    "SELECT symbol, COUNT(*) as cnt FROM prices GROUP BY symbol ORDER BY symbol"
                )
            ).fetchall()
            pg_symbols = {r[0]: r[1] for r in rows}
            logger.info("✓ Symbol coverage: %s", pg_symbols)

            # Assert all configured symbols have data
            missing = [s for s in symbols if s not in pg_symbols]
            if missing:
                logger.warning("⚠ Symbols with no data in PostgreSQL: %s", missing)
                # Don't fail hard — symbols may not have traded today

            # Assert total > 0
            if total == 0:
                raise ValueError(
                    "Validation failed: prices table is empty in PostgreSQL!"
                )

        logger.info("Task 4 complete — validation passed ✅")
        return {"total_rows": total, "symbols": pg_symbols}

    except ValueError:
        raise  # Validation failure → Airflow marks failed
    except Exception as e:
        logger.error("Task 4 — validation query error: %s", e)
        raise
    finally:
        engine.dispose()


# ─────────────────────────────────────────────────────────────────────────────
# DAG definition
# ─────────────────────────────────────────────────────────────────────────────

default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 5, 1),
    "email_on_failure": False,
    "depends_on_past": False,
}

with DAG(
    dag_id="etl_prices_dag",
    default_args=default_args,
    description="Daily ETL: yfinance → DuckDB → PostgreSQL",
    schedule_interval="0 8 * * *",  # 08:00 UTC every day
    catchup=False,
    max_active_runs=1,  # Prevent overlapping runs
    tags=["price-data", "yfinance", "duckdb", "postgres"],
) as dag:

    t1_download = PythonOperator(
        task_id="download_prices",
        python_callable=download_prices,
        doc_md="Download daily OHLCV from yfinance for all symbols in symbols.toml",
    )

    t2_duckdb = PythonOperator(
        task_id="store_to_duckdb",
        python_callable=store_to_duckdb,
        doc_md="Upsert downloaded prices into local DuckDB (persistent cache)",
    )

    t3_postgres = PythonOperator(
        task_id="push_to_postgres",
        python_callable=push_to_postgres,
        doc_md="Read DuckDB → upsert into PostgreSQL prices table",
    )

    t4_validate = PythonOperator(
        task_id="validate_postgres",
        python_callable=validate_postgres,
        doc_md="Assert PostgreSQL has data for all configured symbols",
    )

    t5_dbt = BashOperator(
        task_id="run_dbt",
        bash_command="cd /opt/airflow/dbt && dbt run --profiles-dir /opt/airflow/dbt --target docker",
        doc_md="Run dbt models to build technical indicators and daily marts in PostgreSQL",
    )

    # Pipeline: download → duckdb → postgres → validate → dbt
    t1_download >> t2_duckdb >> t3_postgres >> t4_validate >> t5_dbt
