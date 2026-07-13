"""
Database Utility Functions

Helper functions for database operations — DuckDB and PostgreSQL.
"""

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Table DDL
# ─────────────────────────────────────────────────────────────────────────────

_CREATE_PRICES_DUCKDB = """
CREATE TABLE IF NOT EXISTS prices (
    symbol    TEXT      NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open      DOUBLE    ,
    high      DOUBLE    ,
    low       DOUBLE    ,
    close     DOUBLE    ,
    volume    BIGINT    ,
    PRIMARY KEY (symbol, timestamp)
)
"""

_CREATE_PRICES_POSTGRES = """
CREATE TABLE IF NOT EXISTS prices (
    symbol    VARCHAR(20)  NOT NULL,
    timestamp TIMESTAMPTZ  NOT NULL,
    open      DOUBLE PRECISION,
    high      DOUBLE PRECISION,
    low       DOUBLE PRECISION,
    close     DOUBLE PRECISION,
    volume    BIGINT,
    PRIMARY KEY (symbol, timestamp)
)
"""

_CREATE_PRICES_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_prices_symbol    ON prices (symbol);
CREATE INDEX IF NOT EXISTS idx_prices_timestamp ON prices (timestamp DESC);
"""


def _is_duckdb(connection) -> bool:
    """Return True if connection is a native duckdb.DuckDBPyConnection."""
    try:
        import duckdb
        return isinstance(connection, duckdb.DuckDBPyConnection)
    except ImportError:
        return False


def _is_pg_engine(connection) -> bool:
    """Return True if connection is a SQLAlchemy PostgreSQL engine/connection."""
    dialect = getattr(getattr(connection, 'dialect', None), 'name', '') or ''
    if dialect == 'postgresql':
        return True
    # Try via engine attribute
    dialect2 = getattr(getattr(getattr(connection, 'engine', None), 'dialect', None), 'name', '') or ''
    return dialect2 == 'postgresql'


# ─────────────────────────────────────────────────────────────────────────────
# create_prices_table
# ─────────────────────────────────────────────────────────────────────────────

def create_prices_table(connection) -> None:
    """
    Create the prices table if it doesn't exist.
    Works with a native DuckDB connection or a SQLAlchemy engine/connection.
    """
    if _is_duckdb(connection):
        connection.execute(_CREATE_PRICES_DUCKDB)
        return

    # SQLAlchemy path
    ddl = _CREATE_PRICES_POSTGRES if _is_pg_engine(connection) else _CREATE_PRICES_DUCKDB

    # Engine (has .connect()), use begin()
    if hasattr(connection, 'connect'):
        with connection.begin() as conn:
            conn.execute(text(ddl))
            try:
                conn.execute(text(_CREATE_PRICES_INDEXES))
            except Exception:
                pass  # Indexes optional
        return

    # Already a Connection object
    if hasattr(connection, 'execute'):
        connection.execute(text(ddl))
        return

    logger.error("create_prices_table: unrecognised connection type %s", type(connection))


# ─────────────────────────────────────────────────────────────────────────────
# insert_prices
# ─────────────────────────────────────────────────────────────────────────────

def insert_prices(connection, data: list[dict]) -> int:
    """
    Upsert price records into the prices table.

    Args:
        connection: DuckDB connection OR SQLAlchemy Engine/Connection
        data: List of dicts with keys:
              symbol, timestamp, open, high, low, close, volume

    Returns:
        Number of rows processed (not just inserted — includes updates)
    """
    if not data:
        return 0

    # Normalise to list of param dicts
    records = [
        {
            "symbol":    r.get("symbol"),
            "timestamp": r.get("timestamp"),
            "open":      r.get("open"),
            "high":      r.get("high"),
            "low":       r.get("low"),
            "close":     r.get("close"),
            "volume":    r.get("volume"),
        }
        for r in data
    ]

    # ── DuckDB native path ────────────────────────────────────────────────────
    if _is_duckdb(connection):
        return _insert_duckdb(connection, records)

    # ── SQLAlchemy Engine ─────────────────────────────────────────────────────
    if hasattr(connection, 'connect'):
        # It's an Engine — open a connection
        with connection.begin() as conn:
            return _insert_sqlalchemy(conn, records, pg=_is_pg_engine(connection))

    # ── SQLAlchemy Connection ────────────────────────────────────────────────
    if hasattr(connection, 'execute'):
        return _insert_sqlalchemy(connection, records, pg=_is_pg_engine(connection))

    logger.error("insert_prices: unrecognised connection type %s", type(connection))
    return 0


def _insert_duckdb(conn, records: list[dict]) -> int:
    """Upsert into DuckDB using INSERT OR REPLACE."""
    upsert_sql = """
        INSERT INTO prices (symbol, timestamp, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (symbol, timestamp) DO UPDATE SET
            open   = EXCLUDED.open,
            high   = EXCLUDED.high,
            low    = EXCLUDED.low,
            close  = EXCLUDED.close,
            volume = EXCLUDED.volume
    """
    count = 0
    for r in records:
        try:
            conn.execute(upsert_sql, [
                r["symbol"], r["timestamp"],
                r["open"], r["high"], r["low"], r["close"], r["volume"],
            ])
            count += 1
        except Exception as e:
            logger.debug("DuckDB upsert skip (%s @ %s): %s", r.get("symbol"), r.get("timestamp"), e)
    return count


def _insert_sqlalchemy(conn, records: list[dict], pg: bool = False) -> int:
    """Upsert into PostgreSQL or SQLAlchemy-backed DB."""
    if pg:
        upsert_sql = text("""
            INSERT INTO prices (symbol, timestamp, open, high, low, close, volume)
            VALUES (:symbol, :timestamp, :open, :high, :low, :close, :volume)
            ON CONFLICT (symbol, timestamp) DO UPDATE SET
                open   = EXCLUDED.open,
                high   = EXCLUDED.high,
                low    = EXCLUDED.low,
                close  = EXCLUDED.close,
                volume = EXCLUDED.volume
        """)
    else:
        # Generic SQLAlchemy (e.g. duckdb via SQLAlchemy dialect)
        upsert_sql = text("""
            INSERT OR REPLACE INTO prices (symbol, timestamp, open, high, low, close, volume)
            VALUES (:symbol, :timestamp, :open, :high, :low, :close, :volume)
        """)

    try:
        conn.execute(upsert_sql, records)
        return len(records)
    except Exception as e:
        logger.warning("Bulk upsert failed (%s), falling back to row-by-row: %s", "pg" if pg else "generic", e)
        count = 0
        for r in records:
            try:
                conn.execute(upsert_sql, r)
                count += 1
            except Exception as re:
                logger.debug("Row skip (%s @ %s): %s", r.get("symbol"), r.get("timestamp"), re)
        return count


# ─────────────────────────────────────────────────────────────────────────────
# get_latest_prices
# ─────────────────────────────────────────────────────────────────────────────

def get_latest_prices(connection, symbol: str, limit: int = 100) -> list[dict]:
    """
    Get latest price rows for a symbol.

    Returns:
        List of dicts with keys: symbol, timestamp, open, high, low, close, volume
    """
    sql = (
        f"SELECT symbol, timestamp, open, high, low, close, volume "
        f"FROM prices WHERE symbol = '{symbol}' ORDER BY timestamp DESC LIMIT {limit}"
    )

    if _is_duckdb(connection):
        rows = connection.execute(sql).fetchall()
        return [dict(zip(["symbol", "timestamp", "open", "high", "low", "close", "volume"], r)) for r in rows]

    # SQLAlchemy
    try:
        if hasattr(connection, 'connect'):
            with connection.connect() as conn:
                result = conn.execute(text(sql))
                return [dict(r._mapping) for r in result.fetchall()]
        else:
            result = connection.execute(text(sql))
            return [dict(r._mapping) for r in result.fetchall()]
    except Exception as e:
        logger.warning("get_latest_prices error: %s", e)
        return []
