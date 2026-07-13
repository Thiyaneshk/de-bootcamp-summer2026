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

from app.core.cache.redis_cache import redis_cache


@redis_cache(ttl=300, prefix="prices")
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
    # Delegate to yfinance with 5m interval. Keep simple for phase 1.
    params: dict = {}
    if start_date:
        params["start"] = start_date
    if end_date:
        params["end"] = end_date
    params.update({"interval": "5m", "progress": progress})
    data = yf.download(symbol, **params)
    if data is None or data.empty:
        return pd.DataFrame()
    # Flatten multiindex columns when yfinance returns grouped columns
    if isinstance(data.columns, pd.MultiIndex):
        # MultiIndex from yfinance is typically (Price, Ticker) — keep the Price level
        data.columns = data.columns.get_level_values(0)
    data.index = pd.to_datetime(data.index)
    return data[[c for c in ["Open", "High", "Low", "Close", "Volume"] if c in data.columns]]


@redis_cache(ttl=300, prefix="prices")
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
    params: dict = {}
    # yfinance prefers either period or start/end. Use start/end if provided.
    if start_date:
        params["start"] = start_date
    if end_date:
        params["end"] = end_date
    # Only set period if start/end not provided
    if not (start_date or end_date):
        params["period"] = period
    params.update({"interval": "1d", "progress": False})

    data = yf.download(symbol, **params)
    if data is None or data.empty:
        return pd.DataFrame()

    # Flatten multiindex columns when yfinance returns grouped columns
    if isinstance(data.columns, pd.MultiIndex):
        # MultiIndex from yfinance is typically (Price, Ticker) — keep the Price level
        data.columns = data.columns.get_level_values(0)

    data.index = pd.to_datetime(data.index)
    # Ensure standard OHLCV ordering and presence
    cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in data.columns]
    return data[cols]


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
    # Use yfinance to download multiple symbols at daily interval and return dict
    if not symbols:
        return {}
    data = yf.download(symbols, interval="1d", group_by="ticker", progress=False)
    results: dict[str, pd.DataFrame] = {}
    # If single-symbol-like structure returned (no ticker grouping), normalize
    if isinstance(data.columns, pd.MultiIndex):
        # yfinance returns top-level tickers
        for sym in symbols:
            if sym in data.columns.get_level_values(0):
                sub = data[sym]
                if isinstance(sub.columns, pd.MultiIndex):
                    sub.columns = sub.columns.get_level_values(0)
                sub.index = pd.to_datetime(sub.index)
                results[sym] = sub[[c for c in ["Open", "High", "Low", "Close", "Volume"] if c in sub.columns]]
    else:
        # Single table returned: same for all symbols input (unlikely)
        flat = data
        flat.index = pd.to_datetime(flat.index)
        for sym in symbols:
            results[sym] = flat[[c for c in ["Open", "High", "Low", "Close", "Volume"] if c in flat.columns]]

    return results
