"""
Phase 1: yfinance Data Loading

Extract stock price data from Yahoo Finance API.

TODO: Implement yfinance wrapper functions:
- load_prices_5m(symbol, start_date, end_date) → DataFrame
- load_prices_daily(symbol, start_date, end_date) → DataFrame
- Caching strategy (local file or in-memory)
"""

import pandas as pd
import yfinance as yf


def load_prices_5m(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    progress: bool = True,
) -> pd.DataFrame:
    """
    Load 5-minute interval price data from yfinance.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "BTC-USD")
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        progress: Show download progress bar
    
    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
        
    TODO: Implement logic
    """
    pass


def load_prices_daily(
    symbol: str,
    start_date: str = None,
    end_date: str = None,
    period: str = "1y",
) -> pd.DataFrame:
    """
    Load daily price data from yfinance.
    
    Args:
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        period: Period (1d, 5d, 1mo, 3mo, 6mo, 1y, etc.)
    
    Returns:
        DataFrame with daily OHLCV data
        
    TODO: Implement logic
    """
    pass


def download_multiple_symbols(
    symbols: list[str],
    start_date: str = None,
    end_date: str = None,
) -> dict[str, pd.DataFrame]:
    """
    Download data for multiple symbols.
    
    Args:
        symbols: List of stock symbols
        start_date: Start date
        end_date: End date
    
    Returns:
        Dictionary mapping symbol to DataFrame
        
    TODO: Implement logic with parallel downloads
    """
    pass
