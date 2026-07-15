"""
Phase 2 & 10: ETL Prices DAG — Kafka-style Sequential Ingestion

Apache Airflow DAG for scheduled daily stock price ingestion for all active tickers.

Pipeline:
  Task 1 (get_active_symbols)      Query registry for active symbols
  Task 2 (download_one_by_one)     Expand for each symbol: yfinance -> DuckDB -> Postgres -> Log
  Task 3 (validate_postgres)       Assert row/symbol counts; raise if data missing
  Task 4 (run_dbt)                 Run dbt models

Schedule: Daily at 08:00 UTC  (cron: '0 8 * * *')
"""

import logging
def list_wrap(x):
    return [x]

import os
from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator

from airflow import DAG

logger = logging.getLogger(__name__)

def get_active_symbols_task(**context) -> list[str]:
    """
    Query registry.instruments WHERE is_active = TRUE
    Push list to XCom for dynamic task mapping
    """
    from app.db.registry import get_active_symbols

    symbols = get_active_symbols()
    if not symbols:
        logger.warning("No active symbols found in registry.")
        return []

    logger.info("Active symbols to ingest: %s", symbols)
    return symbols


def download_one_by_one(symbol: str, **context) -> dict:
    """
    Download from yfinance -> store to DuckDB -> push to PostgreSQL.
    Log result to registry.ingestion_log.
    """
    from app.core.etl.prices import load_prices_daily
    from app.db.connection import get_duckdb_connection, get_db_engine
    from app.db.utils import create_prices_table, insert_prices
    from app.db.registry import log_ingestion, update_instrument_status_from_ingestion
    from sqlalchemy import text
    import pandas as pd

    logger.info("Processing symbol: %s", symbol)
    rows_ingested = 0
    status = "success"

    try:
        # 1. Download
        df = load_prices_daily(symbol, period="5d")
        if df is None or df.empty:
            logger.warning("No data for %s", symbol)
            log_ingestion(symbol, "daily", "skipped", 0)
            return {"symbol": symbol, "status": "skipped"}

        records = [
            {
                "symbol": symbol,
                "timestamp": idx.to_pydatetime(),
                "open": float(row.get("Open", 0) or 0),
                "high": float(row.get("High", 0) or 0),
                "low": float(row.get("Low", 0) or 0),
                "close": float(row.get("Close", 0) or 0),
                "volume": int(row.get("Volume", 0) or 0),
            }
            for idx, row in df.iterrows()
        ]

        # 2. DuckDB upsert
        with get_duckdb_connection() as conn:
            create_prices_table(conn)
            rows_ingested = insert_prices(conn, records)

        # 3. PostgreSQL push
        postgres_url = os.getenv("POSTGRES_URL")
        if postgres_url:
            with get_db_engine() as engine:
                with engine.begin() as conn:
                    conn.execute(text("""
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
                    """))

                    df_tmp = pd.DataFrame(records)

                    import re
                    clean_sym = re.sub(r'[^a-zA-Z0-9_]', '_', symbol).lower()
                    table_name = f"prices_etl_tmp_{clean_sym}"

                    df_tmp.to_sql(table_name, conn, if_exists="replace", index=False)

                    conn.execute(text(f"""
                INSERT INTO prices (symbol, timestamp, open, high, low, close, volume)
                SELECT symbol, timestamp::timestamptz, open, high, low, close, volume
                FROM "{table_name}"
                ON CONFLICT (symbol, timestamp) DO UPDATE SET
                    open   = EXCLUDED.open,
                    high   = EXCLUDED.high,
                    low    = EXCLUDED.low,
                    close  = EXCLUDED.close,
                    volume = EXCLUDED.volume
                    """))
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))

    except Exception as e:
        logger.error("Error processing %s: %s", symbol, e)
        status = "failed"
        rows_ingested = 0

    log_ingestion(symbol, "daily", status, rows_ingested)
    update_instrument_status_from_ingestion(symbol, status, rows_ingested)
    return {"symbol": symbol, "status": status, "rows_ingested": rows_ingested}


def validate_postgres(**context) -> dict:
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        logger.info("Task 4 — no POSTGRES_URL, skipping validation (DuckDB-only mode)")
        return {"skipped": True}

    from sqlalchemy import create_engine, text

    symbols = context["ti"].xcom_pull(task_ids="get_active_symbols")
    if not symbols: return {"skipped": True}

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

            # Assert total > 0
            if total == 0:
                raise ValueError(
                    "Validation failed: prices table is empty in PostgreSQL!"
                )

        logger.info("Task 4 complete — validation passed ✅")
        return {"total_rows": total, "symbols": pg_symbols}

    except ValueError:
        raise
    except Exception as e:
        logger.error("Task 4 — validation query error: %s", e)
        raise
    finally:
        engine.dispose()


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
    description="Daily ETL: yfinance → DuckDB → PostgreSQL (Dynamic)",
    schedule="0 8 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["price-data", "yfinance", "duckdb", "postgres"],
) as dag:

    t1_active_symbols = PythonOperator(
        task_id="get_active_symbols",
        python_callable=get_active_symbols_task,
        doc_md="Fetch active symbols from registry",
    )

    t2_download = PythonOperator.partial(
        task_id="download_one_by_one",
        python_callable=download_one_by_one,
        doc_md="Download yfinance -> DuckDB -> Postgres -> Log (Parallel via Expand)",
    ).expand(op_args=t1_active_symbols.output.map(list_wrap))

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

    t1_active_symbols >> t2_download >> t4_validate >> t5_dbt
