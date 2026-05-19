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


def refresh_all():
    """Refresh data for all configured symbols."""
    # TODO: Load symbols from config/symbols.toml
    # TODO: Download prices for each symbol
    # TODO: Insert into database
    # TODO: Log results
    pass


def refresh_symbols(symbols: list[str]):
    """Refresh data for specific symbols."""
    # TODO: Implement for specified symbols
    pass


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
