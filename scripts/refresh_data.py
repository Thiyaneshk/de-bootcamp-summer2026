"""
Phase 2: Manual ETL Refresh Script

CLI entry point for manually running the ETL pipeline.

TODO: Implement:
- Load yfinance data for configured symbols
- Validate data quality
- Insert into PostgreSQL
- Log execution
- Handle errors gracefully

Usage:
    uv run python -m scripts.refresh_data --symbols AAPL,MSFT,GOOGL
    uv run python -m scripts.refresh_data --all
"""

import argparse
import logging
import os
from datetime import datetime, timedelta

import tomllib

from app.core.etl.prices import load_prices_daily
from app.db.connection import get_db_engine
from app.db.utils import create_prices_table, insert_prices, get_latest_prices


def refresh_all():
    """Refresh data for all configured symbols."""
    cfg_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'symbols.toml')
    if not os.path.exists(cfg_path):
        logging.error("symbols.toml not found: %s", cfg_path)
        return

    with open(cfg_path, 'rb') as f:
        cfg = tomllib.load(f)

    symbols = cfg.get('default', {}).get('symbols', [])
    if not symbols:
        logging.info('No symbols to refresh')
        return

    refresh_symbols(symbols)


def refresh_symbols(symbols: list[str]):
    """Refresh data for specific symbols."""
    logging.info('Refreshing symbols: %s', symbols)

    # Use DB engine context manager
    with get_db_engine() as engine:
        # Ensure prices table exists
        try:
            create_prices_table(engine)
        except Exception as e:
            logging.error('Failed to create prices table: %s', e)

        for sym in symbols:
            try:
                # Determine start_date from DB latest
                latest = get_latest_prices(engine, sym, limit=1)
                if latest and len(latest) > 0:
                    last_ts = latest[0]['timestamp']
                    if isinstance(last_ts, str):
                        start_date = last_ts.split('T')[0]
                    else:
                        start_date = datetime.fromisoformat(str(last_ts)).date().isoformat()
                    # Add one day to avoid duplicate row collisions
                    start_dt = datetime.fromisoformat(start_date) + timedelta(days=1)
                    start_iso = start_dt.date().isoformat()
                    df = load_prices_daily(sym, start_date=start_iso)
                else:
                    # No data present -> pull 1y by default
                    df = load_prices_daily(sym, period='1y')

                if df is None or df.empty:
                    logging.info('No data returned for %s', sym)
                    continue

                # Prepare records
                records = []
                for idx, row in df.iterrows():
                    records.append({
                        'symbol': sym,
                        'timestamp': idx.to_pydatetime(),
                        'open': float(row.get('Open', None)) if 'Open' in row.index else None,
                        'high': float(row.get('High', None)) if 'High' in row.index else None,
                        'low': float(row.get('Low', None)) if 'Low' in row.index else None,
                        'close': float(row.get('Close', None)) if 'Close' in row.index else None,
                        'volume': int(row.get('Volume', 0)) if 'Volume' in row.index else None,
                    })

                inserted = insert_prices(engine, records)
                logging.info('Upserted %d rows for %s', inserted, sym)
            except Exception as e:
                logging.exception('Error refreshing %s: %s', sym, e)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='ETL data refresh script')
    parser.add_argument('--symbols', type=str, help='Comma-separated symbols to refresh')
    parser.add_argument('--all', action='store_true', help='Refresh all symbols')
    
    args = parser.parse_args()
    
    if args.all:
        refresh_all()
    elif args.symbols:
        symbols = args.symbols.split(',')
        refresh_symbols(symbols)
    else:
        print("Please specify --symbols or --all")


if __name__ == '__main__':
    main()
