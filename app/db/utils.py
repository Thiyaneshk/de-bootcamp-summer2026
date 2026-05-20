"""
Phase 1: Database Utility Functions

Helper functions for database operations.

TODO: Implement utilities:
- Create tables
- Insert bulk data
- Query data with filtering
- Data validation
"""

from sqlalchemy import text


def create_prices_table(connection) -> None:
    """
    Create prices table in database.
    
    Args:
        connection: Database connection
        
    TODO: Create table with columns:
    - symbol (VARCHAR)
    - timestamp (TIMESTAMP)
    - open, high, low, close (FLOAT)
    - volume (BIGINT)
    """
    # Accept either SQLAlchemy Engine/Connection or duckdb.Connection
    create_sql = """
    CREATE TABLE IF NOT EXISTS prices (
        symbol TEXT NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        open DOUBLE PRECISION,
        high DOUBLE PRECISION,
        low DOUBLE PRECISION,
        close DOUBLE PRECISION,
        volume BIGINT,
        PRIMARY KEY (symbol, timestamp)
    )
    """

    # Try SQLAlchemy Engine/Connection first
    try:
        # If it has .connect(), it's an Engine
        if hasattr(connection, 'connect'):
            with connection.begin() as conn:
                conn.execute(text(create_sql))
            return
        # If it has .execute() and .begin(), it's a Connection
        elif hasattr(connection, 'execute') and hasattr(connection, 'begin'):
            with connection.begin():
                connection.execute(text(create_sql))
            return
    except Exception as e:
        pass

    # duckdb connection fallback
    try:
        connection.execute(create_sql)
    except Exception:
        # last-resort: open duckdb connection and execute
        import duckdb

        db_path = "data/app.duckdb"
        conn = duckdb.connect(db_path)
        conn.execute(create_sql)
        conn.close()


def insert_prices(connection, data: list[dict]) -> int:
    """
    Insert price records into database.
    
    Args:
        connection: Database connection
        data: List of price dictionaries
    
    Returns:
        Number of rows inserted
        
    TODO: Implement bulk insert
    """
    if not data:
        return 0

    # Normalize input to list of tuples
    rows = []
    for r in data:
        rows.append((r.get('symbol'), r.get('timestamp'), r.get('open'), r.get('high'), r.get('low'), r.get('close'), r.get('volume')))

    # If SQLAlchemy engine/connection provided and is Postgres, use ON CONFLICT
    try:
        dialect = getattr(connection, 'dialect', None)
        if dialect is not None and getattr(dialect, 'name', '') == 'postgresql':
            # Use COPY-like bulk insert via executemany with ON CONFLICT
            insert_sql = text("""
            INSERT INTO prices (symbol, timestamp, open, high, low, close, volume)
            VALUES (:symbol, :timestamp, :open, :high, :low, :close, :volume)
            ON CONFLICT (symbol, timestamp) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
            """)
            conn = connection.connect() if hasattr(connection, 'connect') else connection
            with conn.begin() as trans:
                conn.execute(insert_sql, [
                    {
                        'symbol': r[0],
                        'timestamp': r[1],
                        'open': r[2],
                        'high': r[3],
                        'low': r[4],
                        'close': r[5],
                        'volume': r[6],
                    }
                    for r in rows
                ])
            try:
                conn.close()
            except Exception:
                pass
            return len(rows)
    except Exception as e:
        import logging
        logging.warning(f"Postgres ON CONFLICT upsert failed (will retry with fallback): {e}")
        pass
    # If SQLAlchemy Engine/Connection (non-Postgres) do simple inserts
    try:
        if hasattr(connection, 'connect'):
            conn = connection.connect()
            insert_sql = "INSERT INTO prices (symbol, timestamp, open, high, low, close, volume) VALUES (:symbol, :timestamp, :open, :high, :low, :close, :volume)"
            with conn.begin():
                conn.execute(insert_sql, [
                    {
                        'symbol': r[0],
                        'timestamp': r[1],
                        'open': r[2],
                        'high': r[3],
                        'low': r[4],
                        'close': r[5],
                        'volume': r[6],
                    }
                    for r in rows
                ])
            try:
                conn.close()
            except Exception:
                pass
            return len(rows)
    except Exception:
        pass

    # Fallback: duckdb connection without SQLAlchemy
    try:
        if hasattr(connection, 'execute') and not hasattr(connection, 'connect'):
            for r in rows:
                connection.execute("INSERT INTO prices VALUES (?, ?, ?, ?, ?, ?, ?)", r)
            return len(rows)
    except Exception:
        pass

    # Last-resort: open a SQLAlchemy engine from env and use simple inserts
    from sqlalchemy import create_engine
    import os

    pg = os.getenv('POSTGRES_URL')
    if pg:
        engine = create_engine(pg)
        with engine.connect() as conn:
            insert_sql = text(
                "INSERT INTO prices (symbol, timestamp, open, high, low, close, volume) VALUES (:symbol, :timestamp, :open, :high, :low, :close, :volume)"
            )
            with conn.begin():
                conn.execute(insert_sql, [
                    {
                        'symbol': r[0],
                        'timestamp': r[1],
                        'open': r[2],
                        'high': r[3],
                        'low': r[4],
                        'close': r[5],
                        'volume': r[6],
                    }
                    for r in rows
                ])
        return len(rows)

    return 0


def get_latest_prices(connection, symbol: str, limit: int = 100) -> list[dict]:
    """
    Get latest price data for a symbol.
    
    Args:
        connection: Database connection
        symbol: Stock symbol
        limit: Maximum rows to return
    
    Returns:
        List of price records
        
    TODO: Implement query
    """
    try:
        # SQLAlchemy engine
        conn = connection.connect() if hasattr(connection, 'connect') else connection
        res = conn.execute(f"SELECT symbol, timestamp, open, high, low, close, volume FROM prices WHERE symbol = '{symbol}' ORDER BY timestamp DESC LIMIT {limit}")
        rows = [dict(r) for r in res.fetchall()]
        try:
            conn.close()
        except Exception:
            pass
        return rows
    except Exception:
        # duckdb fallback
        try:
            res = connection.execute(f"SELECT symbol, timestamp, open, high, low, close, volume FROM prices WHERE symbol = '{symbol}' ORDER BY timestamp DESC LIMIT {limit}").fetchall()
            return [dict(zip(['symbol','timestamp','open','high','low','close','volume'], r)) for r in res]
        except Exception:
            return []
