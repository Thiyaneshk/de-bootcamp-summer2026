"""
Database Tests

Test database connections and operations.
"""

import os
import pytest

import duckdb
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

from app.db.connection import get_db_engine


@pytest.fixture
def postgres_url(monkeypatch):
    """Fixture to set a valid PostgreSQL URL for tests."""
    monkeypatch.setenv(
        "POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
    )


def test_duckdb_connection(monkeypatch):
    """Test DuckDB connection."""
    # create a random path instead of NamedTemporaryFile to avoid "not a valid DuckDB" when it touches an empty file
    import uuid

    db_path = f"/tmp/{uuid.uuid4()}.duckdb"

    # Override POSTGRES_URL to ensure DuckDB engine
    monkeypatch.setenv("POSTGRES_URL", "")
    monkeypatch.setenv("DUCKDB_PATH", db_path)

    try:
        with get_db_engine() as engine:
            assert isinstance(engine, Engine) or isinstance(
                engine, duckdb.DuckDBPyConnection
            )

            try:
                res = engine.execute("SELECT 1 as val").fetchall()
            except Exception:
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
    conn.execute("""
        CREATE TABLE prices (
            symbol VARCHAR,
            timestamp TIMESTAMP,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT,
            volume BIGINT
        )
    """)

    conn.execute("""
        INSERT INTO prices VALUES ('AAPL', NOW(), 189.5, 189.8, 189.4, 189.6, 1000000)
    """)

    result = conn.execute("SELECT count(*) FROM prices").fetchone()
    assert result[0] == 1

    conn.close()


def test_postgres_connection(postgres_url):
    """Test PostgreSQL connection."""
    with get_db_engine() as engine:
        assert isinstance(engine, Engine)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT 1 as val")).fetchall()
            assert res[0][0] == 1


def test_postgres_table_creation(postgres_url):
    """Test PostgreSQL table creation."""
    with get_db_engine() as engine:
        with engine.connect() as conn:
            # Clean up first in case of previous run failure
            conn.execute(text("DROP TABLE IF EXISTS test_table"))
            conn.commit()

            conn.execute(
                text("""
                CREATE TABLE test_table (
                    id SERIAL PRIMARY KEY,
                    val TEXT
                )
            """)
            )
            conn.commit()

            # Check if table exists using SQLAlchemy inspector
            inspector = inspect(engine)
            assert "test_table" in inspector.get_table_names()

            # Clean up
            conn.execute(text("DROP TABLE test_table"))
            conn.commit()


def test_postgres_data_insertion(postgres_url):
    """Test PostgreSQL data insertion."""
    with get_db_engine() as engine:
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS test_table"))
            conn.commit()

            conn.execute(
                text("""
                CREATE TABLE test_table (
                    id SERIAL PRIMARY KEY,
                    val TEXT
                )
            """)
            )
            conn.execute(text("INSERT INTO test_table (val) VALUES ('hello')"))
            conn.commit()

            res = conn.execute(text("SELECT count(*) FROM test_table")).fetchone()
            assert res[0] == 1

            res = conn.execute(text("SELECT val FROM test_table LIMIT 1")).fetchone()
            assert res[0] == "hello"

            # Clean up
            conn.execute(text("DROP TABLE test_table"))
            conn.commit()
