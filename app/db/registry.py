"""Registry helpers for instruments, index constituents, and ingestion history."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import duckdb
from sqlalchemy import create_engine, text

from app.db.connection import get_duckdb_connection


def _get_postgres_engine():
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        return None
    return create_engine(postgres_url, pool_pre_ping=True)


def _ensure_schema_sql() -> str:
    return """
    CREATE TABLE IF NOT EXISTS instruments (
        symbol VARCHAR(50) PRIMARY KEY,
        name VARCHAR(200),
        instrument_type VARCHAR(20) NOT NULL,
        exchange VARCHAR(50),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS index_constituents (
        index_symbol VARCHAR(50) NOT NULL,
        stock_symbol VARCHAR(50) NOT NULL,
        weight DECIMAL(8,4),
        added_date DATE,
        removed_date DATE,
        PRIMARY KEY (index_symbol, stock_symbol)
    );
    CREATE TABLE IF NOT EXISTS ingestion_log (
        id INTEGER,
        symbol VARCHAR(50) NOT NULL,
        ingestion_type VARCHAR(20),
        status VARCHAR(20),
        rows_ingested INTEGER DEFAULT 0,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    );
    """


def init_registry_tables(connection: Any | None = None) -> None:
    """Create the registry tables in DuckDB or PostgreSQL."""
    postgres_url = os.getenv("POSTGRES_URL")
    if connection is None:
        if postgres_url:
            engine = _get_postgres_engine()
            if engine is None:
                return
            with engine.begin() as conn:
                conn.execute(text(_ensure_schema_sql()))
            engine.dispose()
        else:
            with get_duckdb_connection() as conn:
                conn.execute(_ensure_schema_sql())
        return

    if hasattr(connection, "connect") and not isinstance(connection, duckdb.DuckDBPyConnection):
        with connection.begin() as conn:
            conn.execute(text(_ensure_schema_sql()))
        return

    connection.execute(_ensure_schema_sql())


def add_instrument(
    symbol: str,
    name: str | None = None,
    instrument_type: str = "stock",
    exchange: str | None = None,
    is_active: bool = True,
) -> dict[str, Any]:
    """Insert or update an instrument record."""
    init_registry_tables()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        engine = _get_postgres_engine()
        if engine is None:
            return {}
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO instruments (
                        symbol, name, instrument_type, exchange, is_active, created_at, updated_at
                    ) VALUES (:symbol, :name, :instrument_type, :exchange, :is_active, :now, :now)
                    ON CONFLICT (symbol) DO UPDATE SET
                        name = EXCLUDED.name,
                        instrument_type = EXCLUDED.instrument_type,
                        exchange = EXCLUDED.exchange,
                        is_active = EXCLUDED.is_active,
                        updated_at = :now
                    """
                ),
                {
                    "symbol": symbol,
                    "name": name,
                    "instrument_type": instrument_type,
                    "exchange": exchange,
                    "is_active": is_active,
                    "now": now,
                },
            )
        engine.dispose()
    else:
        with get_duckdb_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO instruments (
                    symbol, name, instrument_type, exchange, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    symbol,
                    name,
                    instrument_type,
                    exchange,
                    is_active,
                    now,
                    now,
                ],
            )
    return {
        "symbol": symbol,
        "name": name,
        "instrument_type": instrument_type,
        "exchange": exchange,
        "is_active": is_active,
    }


def get_instruments(
    instrument_type: str | None = None,
    active_only: bool = False,
) -> list[dict[str, Any]]:
    """Return registered instruments as a list of dictionaries."""
    init_registry_tables()
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        engine = _get_postgres_engine()
        if engine is None:
            return []
        with engine.connect() as conn:
            query = "SELECT symbol, name, instrument_type, exchange, is_active FROM instruments"
            if instrument_type:
                query += " WHERE instrument_type = :instrument_type"
            if active_only:
                query += " WHERE is_active = TRUE" if not instrument_type else " AND is_active = TRUE"
            query += " ORDER BY symbol"
            result = conn.execute(text(query), {"instrument_type": instrument_type} if instrument_type else {})
            rows = result.fetchall()
        engine.dispose()
        return [
            {
                "symbol": row[0],
                "name": row[1],
                "instrument_type": row[2],
                "exchange": row[3],
                "is_active": row[4],
            }
            for row in rows
        ]

    with get_duckdb_connection() as conn:
        query = "SELECT symbol, name, instrument_type, exchange, is_active FROM instruments"
        clauses: list[str] = []
        if instrument_type:
            clauses.append("instrument_type = ?")
        if active_only:
            clauses.append("is_active = TRUE")
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY symbol"
        params = [instrument_type] if instrument_type else []
        result = conn.execute(query, params)
        rows = result.fetchall()

    return [
        {
            "symbol": row[0],
            "name": row[1],
            "instrument_type": row[2],
            "exchange": row[3],
            "is_active": row[4],
        }
        for row in rows
    ]


def set_instrument_active(symbol: str, is_active: bool) -> None:
    """Toggle an instrument's active flag."""
    init_registry_tables()
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        engine = _get_postgres_engine()
        if engine is None:
            return
        with engine.begin() as conn:
            conn.execute(
                text(
                    "UPDATE instruments SET is_active = :is_active, updated_at = NOW() WHERE symbol = :symbol"
                ),
                {"is_active": is_active, "symbol": symbol},
            )
        engine.dispose()
    else:
        with get_duckdb_connection() as conn:
            conn.execute(
                "UPDATE instruments SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE symbol = ?",
                [is_active, symbol],
            )


def get_active_symbols() -> list[str]:
    """Return the active instruments that should be ingested."""
    instruments = get_instruments(active_only=True)
    return [item["symbol"] for item in instruments if item.get("symbol")]


def upsert_index_constituents(index_symbol: str, constituents: list[dict[str, Any]]) -> None:
    """Store index membership rows for a given index symbol."""
    init_registry_tables()
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        engine = _get_postgres_engine()
        if engine is None:
            return
        with engine.begin() as conn:
            for item in constituents:
                conn.execute(
                    text(
                        """
                        INSERT INTO index_constituents (index_symbol, stock_symbol, weight, added_date, removed_date)
                        VALUES (:index_symbol, :stock_symbol, :weight, :added_date, :removed_date)
                        ON CONFLICT (index_symbol, stock_symbol) DO UPDATE SET
                            weight = EXCLUDED.weight,
                            added_date = EXCLUDED.added_date,
                            removed_date = EXCLUDED.removed_date
                        """
                    ),
                    {
                        "index_symbol": index_symbol,
                        "stock_symbol": item.get("stock_symbol"),
                        "weight": item.get("weight"),
                        "added_date": item.get("added_date"),
                        "removed_date": item.get("removed_date"),
                    },
                )
        engine.dispose()
        return

    with get_duckdb_connection() as conn:
        for item in constituents:
            conn.execute(
                """
                INSERT OR REPLACE INTO index_constituents (
                    index_symbol, stock_symbol, weight, added_date, removed_date
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    index_symbol,
                    item.get("stock_symbol"),
                    item.get("weight"),
                    item.get("added_date"),
                    item.get("removed_date"),
                ],
            )


def log_ingestion(
    symbol: str,
    ingestion_type: str,
    status: str,
    rows_ingested: int = 0,
    completed_at: datetime | None = None,
) -> list[dict[str, Any]]:
    """Record an ingestion result and return the recent log entries."""
    init_registry_tables()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    completed = completed_at or datetime.now(timezone.utc)
    completed_str = completed.strftime("%Y-%m-%d %H:%M:%S")
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        engine = _get_postgres_engine()
        if engine is None:
            return []
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO ingestion_log (symbol, ingestion_type, status, rows_ingested, started_at, completed_at)
                    VALUES (:symbol, :ingestion_type, :status, :rows_ingested, :started_at, :completed_at)
                    """
                ),
                {
                    "symbol": symbol,
                    "ingestion_type": ingestion_type,
                    "status": status,
                    "rows_ingested": rows_ingested,
                    "started_at": now,
                    "completed_at": completed_str,
                },
            )
            rows = conn.execute(
                text(
                    "SELECT symbol, ingestion_type, status, rows_ingested, started_at, completed_at FROM ingestion_log ORDER BY id DESC LIMIT 10"
                )
            ).fetchall()
        engine.dispose()
        return [
            {
                "symbol": row[0],
                "ingestion_type": row[1],
                "status": row[2],
                "rows_ingested": row[3],
                "started_at": row[4],
                "completed_at": row[5],
            }
            for row in rows
        ]

    with get_duckdb_connection() as conn:
        conn.execute(
            """
            INSERT INTO ingestion_log (symbol, ingestion_type, status, rows_ingested, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [symbol, ingestion_type, status, rows_ingested, now, completed_str],
        )
        rows = conn.execute(
            "SELECT symbol, ingestion_type, status, rows_ingested, started_at, completed_at FROM ingestion_log ORDER BY id DESC LIMIT 10"
        ).fetchall()

    return [
        {
            "symbol": row[0],
            "ingestion_type": row[1],
            "status": row[2],
            "rows_ingested": row[3],
            "started_at": row[4],
            "completed_at": row[5],
        }
        for row in rows
    ]
