"""
pg_loader.py — DuckDB → PostgreSQL ETL helper

Reusable module used by:
  - app/views/03_Data_Explorer.py  (manual push from UI)
  - scripts/schedule_pg_sync.py    (automated daily sync)

Usage (programmatic):
    from scripts.pg_loader import sync_symbols_to_postgres
    sync_symbols_to_postgres(["AAPL", "MSFT"], pg_url="postgresql+psycopg2://...")
"""

import logging
import os
from datetime import datetime, timedelta

import duckdb
import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/app.duckdb")

# ── DuckDB read ───────────────────────────────────────────────────────────────


def fetch_from_duckdb(symbols: list[str], days_back: int = 7) -> pd.DataFrame:
    """
    Read recent price data from DuckDB for the given symbols.

    Args:
        symbols:   List of stock tickers, e.g. ["AAPL", "MSFT"]
        days_back: How many calendar days back to fetch (default 7).
                   Use a large number (e.g. 3650) to fetch all history.

    Returns:
        DataFrame with columns: symbol, timestamp, open, high, low, close, volume
    """
    if not symbols:
        return pd.DataFrame()

    if not os.path.exists(DUCKDB_PATH):
        logger.warning("DuckDB file not found at %s", DUCKDB_PATH)
        return pd.DataFrame()

    conn = duckdb.connect(DUCKDB_PATH)
    try:
        # Check table exists
        exists = conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name = 'prices'"
        ).fetchone()[0]
        if not exists:
            logger.warning("prices table does not exist in DuckDB")
            conn.close()
            return pd.DataFrame()

        cutoff = (datetime.utcnow() - timedelta(days=days_back)).date().isoformat()
        placeholders = ", ".join(["?"] * len(symbols))
        df = conn.execute(
            f"""
            SELECT symbol, timestamp, open, high, low, close, volume
            FROM prices
            WHERE symbol IN ({placeholders})
              AND timestamp >= ?
            ORDER BY symbol, timestamp
            """,
            list(symbols) + [cutoff],
        ).df()
        logger.info("Fetched %d rows from DuckDB for %s", len(df), symbols)
        return df
    finally:
        conn.close()


# ── yfinance → DuckDB → PostgreSQL pipeline ───────────────────────────────────


def refresh_and_sync(
    symbols: list[str],
    pg_url: str,
    period: str = "5d",
) -> dict:
    """
    Full pipeline:
      1. Download fresh data from yfinance
      2. Store in DuckDB (upsert)
      3. Push DuckDB data to PostgreSQL (upsert)

    Args:
        symbols: List of tickers
        pg_url:  SQLAlchemy PostgreSQL URL
        period:  yfinance period string (default "5d")

    Returns:
        dict with keys: symbols, yf_rows, pg_rows, errors
    """
    from app.core.etl.prices import load_prices_daily
    from app.db.connection import get_duckdb_connection
    from app.db.utils import create_prices_table, insert_prices

    result = {"symbols": symbols, "yf_rows": 0, "pg_rows": 0, "errors": []}

    # ── Step 1: yfinance → DuckDB ────────────────────────────────────────────
    with get_duckdb_connection() as duck_conn:
        create_prices_table(duck_conn)

        for sym in symbols:
            try:
                df = load_prices_daily(sym, period=period)
                if df is None or df.empty:
                    logger.warning("No yfinance data for %s", sym)
                    continue

                records = []
                for idx, row in df.iterrows():
                    records.append(
                        {
                            "symbol": sym,
                            "timestamp": idx.to_pydatetime(),
                            "open": float(row.get("Open", 0) or 0),
                            "high": float(row.get("High", 0) or 0),
                            "low": float(row.get("Low", 0) or 0),
                            "close": float(row.get("Close", 0) or 0),
                            "volume": int(row.get("Volume", 0) or 0),
                        }
                    )

                inserted = insert_prices(duck_conn, records)
                result["yf_rows"] += inserted
                logger.info("DuckDB: upserted %d rows for %s", inserted, sym)

            except Exception as e:
                msg = f"yfinance/DuckDB error for {sym}: {e}"
                logger.exception(msg)
                result["errors"].append(msg)

    # ── Step 2: DuckDB → PostgreSQL ──────────────────────────────────────────
    if not pg_url:
        logger.info("No POSTGRES_URL — skipping PostgreSQL sync")
        return result

    try:
        df_all = fetch_from_duckdb(symbols, days_back=30)
        if df_all.empty:
            logger.warning(
                "Nothing to push to PostgreSQL — DuckDB query returned empty"
            )
            return result

        engine = create_engine(pg_url, pool_pre_ping=True)

        # Ensure table exists in Postgres
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

        # Upsert via temp table
        with engine.begin() as conn:
            df_all.to_sql("prices_tmp", conn, if_exists="replace", index=False)
            upsert = text("""
                INSERT INTO prices (symbol, timestamp, open, high, low, close, volume)
                SELECT symbol, timestamp::timestamptz, open, high, low, close, volume
                FROM prices_tmp
                ON CONFLICT (symbol, timestamp) DO UPDATE SET
                    open   = EXCLUDED.open,
                    high   = EXCLUDED.high,
                    low    = EXCLUDED.low,
                    close  = EXCLUDED.close,
                    volume = EXCLUDED.volume
            """)
            conn.execute(upsert)
            conn.execute(text("DROP TABLE IF EXISTS prices_tmp"))

        result["pg_rows"] = len(df_all)
        logger.info("PostgreSQL: upserted %d rows", len(df_all))
        engine.dispose()

    except Exception as e:
        msg = f"PostgreSQL push error: {e}"
        logger.exception(msg)
        result["errors"].append(msg)

    return result


# ── Convenience aliases used by schedule_pg_sync.py ──────────────────────────


def sync_symbols_to_postgres(
    symbols: list[str], pg_url: str | None = None, period: str = "5d"
) -> dict:
    """Convenience wrapper — pulls POSTGRES_URL from env if not provided."""
    url = pg_url or os.getenv("POSTGRES_URL", "")
    if not url:
        raise RuntimeError(
            "POSTGRES_URL is not set. "
            "Either pass pg_url= or set the POSTGRES_URL environment variable."
        )
    return refresh_and_sync(symbols, url, period=period)


def sync_all_from_config(pg_url: str | None = None, period: str = "5d") -> dict:
    """Load symbols from config/symbols.toml and run the full sync."""
    import tomllib

    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config", "symbols.toml")
    try:
        with open(cfg_path, "rb") as f:
            cfg = tomllib.load(f)
        symbols = cfg.get("default", {}).get("symbols", [])
    except Exception as e:
        logger.error("Could not read symbols.toml: %s", e)
        symbols = []

    if not symbols:
        logger.warning("No symbols found in symbols.toml [default] section")
        return {
            "symbols": [],
            "yf_rows": 0,
            "pg_rows": 0,
            "errors": ["No symbols configured"],
        }

    return sync_symbols_to_postgres(symbols, pg_url=pg_url, period=period)
