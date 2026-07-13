"""
Phase 2: Database Initialization Script

Create PostgreSQL schema and tables for the application.

TODO: Implement:
- Connect to PostgreSQL
- Create tables:
  - prices (symbol, timestamp, open, high, low, close, volume)
  - watchlist (user_id, symbol, added_date)
  - trading_signals (symbol, signal_type, timestamp)
- Create indexes
- Set up foreign keys

Usage:
    uv run python scripts/init_db.py
"""

import logging

from app.db.connection import get_db_engine
from app.db.utils import create_prices_table


def init_database():
    """Initialize PostgreSQL database schema."""
    logging.info('Initializing database schema')
    # Create tables using DB engine
    with get_db_engine() as engine:
        try:
            create_prices_table(engine)
            logging.info('Created or verified prices table')
        except Exception as e:
            logging.exception('Failed to create prices table: %s', e)

    logging.info('Database initialization complete')


if __name__ == '__main__':
    init_database()
