"""
Database Tests

Test database connections and operations.

TODO: Implement tests:
- Test DuckDB connection
- Test PostgreSQL connection
- Test table creation
- Test data insertion
"""

import os

import duckdb

from app.db.connection import get_db_engine


def test_duckdb_connection():
    """Test DuckDB connection."""
    # create a random path instead of NamedTemporaryFile to avoid "not a valid DuckDB" when it touches an empty file
    import uuid

    db_path = f"/tmp/{uuid.uuid4()}.duckdb"

    # Override POSTGRES_URL to ensure DuckDB engine
    os.environ["POSTGRES_URL"] = ""
    os.environ["DUCKDB_PATH"] = db_path

    try:
        with get_db_engine() as engine:
            from sqlalchemy.engine import Engine

            assert isinstance(engine, Engine) or isinstance(
                engine, duckdb.DuckDBPyConnection
            )

            try:
                res = engine.execute("SELECT 1 as val").fetchall()
            except Exception:
                from sqlalchemy import text

                with engine.connect() as conn:
                    res = conn.execute(text("SELECT 1 as val")).fetchall()

            assert res[0][0] == 1
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass


def test_insert_prices():
    """Test inserting price data."""
    conn = duckdb.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE prices (
            symbol VARCHAR,
            timestamp TIMESTAMP,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT,
            volume BIGINT
        )
    """
    )

    conn.execute(
        """
        INSERT INTO prices VALUES ('AAPL', NOW(), 189.5, 189.8, 189.4, 189.6, 1000000)
    """
    )

    result = conn.execute("SELECT count(*) FROM prices").fetchone()
    assert result[0] == 1

    conn.close()
