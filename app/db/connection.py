"""
Phase 1: Database Connection Abstraction

Dual-backend database support:
- DuckDB (Phase 1, local development)
- PostgreSQL (Phase 2+, production)
"""

import os
from contextlib import contextmanager

import duckdb
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Load environment variables from .env file
load_dotenv()


@contextmanager
def get_duckdb_connection():
    """
    Get DuckDB connection (Phase 1).

    Yields:
        DuckDB connection object
    """
    db_path = os.getenv("DUCKDB_PATH", "data/app.duckdb")
    # Ensure parent directory exists
    parent = os.path.dirname(db_path)
    if parent and not os.path.exists(parent):
        try:
            os.makedirs(parent, exist_ok=True)
        except Exception:
            pass

    conn = duckdb.connect(db_path)
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


@contextmanager
def get_postgres_engine() -> Engine:
    """
    Get SQLAlchemy PostgreSQL engine (Phase 2+).

    Yields:
        SQLAlchemy Engine object
    """
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        raise RuntimeError("POSTGRES_URL not set in environment")

    # Create SQLAlchemy engine
    engine = create_engine(postgres_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        try:
            engine.dispose()
        except Exception:
            pass


@contextmanager
def get_db_engine() -> Engine:
    """
    Get database engine based on environment.

    Automatically switches between DuckDB and PostgreSQL based on
    POSTGRES_URL environment variable.

    Yields:
        Database engine (DuckDB or PostgreSQL)
    """
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        with get_postgres_engine() as engine:
            yield engine
    else:
        # For DuckDB, return a SQLAlchemy engine backed by DuckDB if available,
        # else provide a duckdb Connection object via context manager above.
        duckdb_path = os.getenv("DUCKDB_PATH", "data/app.duckdb")
        try:
            # Use duckdb SQLAlchemy URL if duckdb dialect is available
            url = f"duckdb:///{duckdb_path}"
            engine = create_engine(url)
            yield engine
        except Exception:
            # Fallback to duckdb connection
            with get_duckdb_connection() as conn:
                yield conn


def execute_query(query: str, db_type: str = "auto") -> list:
    """
    Execute a SQL query on the configured database.

    Args:
        query: SQL query string
        db_type: "auto", "duckdb", or "postgres"

    Returns:
        Query result rows

    TODO: Implement query execution
    """
    db_type = db_type.lower()
    if db_type == "auto":
        postgres_url = os.getenv("POSTGRES_URL")
        db_type = "postgres" if postgres_url else "duckdb"

    if db_type == "postgres":
        postgres_url = os.getenv("POSTGRES_URL")
        if not postgres_url:
            raise RuntimeError("POSTGRES_URL not set for postgres execution")
        engine = create_engine(postgres_url)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            try:
                return result.fetchall()
            except Exception:
                return []
    elif db_type == "duckdb":
        db_path = os.getenv("DUCKDB_PATH", "data/app.duckdb")
        conn = duckdb.connect(db_path)
        try:
            result = conn.execute(query).fetchall()
            return result
        finally:
            try:
                conn.close()
            except Exception:
                pass
    else:
        raise ValueError("db_type must be 'auto', 'duckdb' or 'postgres'")
