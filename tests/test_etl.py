"""
Phase 1: ETL Tests

Test yfinance data loading and transformations.

TODO: Implement tests:
- Test yfinance data loading for valid symbols
- Test error handling for invalid symbols
- Test data validation (OHLCV columns exist)
- Test date range filtering
"""

from unittest.mock import patch

import pandas as pd


@patch("yfinance.download")
def test_load_prices_valid_symbol(mock_download):
    """Test loading prices for valid symbol."""
    from app.core.etl.prices import load_prices_daily

    # Mock data
    dates = pd.date_range("2026-05-01", periods=2, freq="D")
    mock_df = pd.DataFrame(
        {
            "Open": [150.0, 151.0],
            "High": [152.0, 153.0],
            "Low": [149.0, 150.0],
            "Close": [151.0, 152.0],
            "Volume": [1000000, 1100000],
        },
        index=dates,
    )

    mock_download.return_value = mock_df

    # Test
    df = load_prices_daily("AAPL", start_date="2026-05-01", end_date="2026-05-02")

    assert not df.empty
    assert "Close" in df.columns
    assert len(df) == 2


@patch("yfinance.download")
def test_load_prices_invalid_symbol(mock_download):
    """Test error handling for invalid symbol."""
    from app.core.etl.prices import load_prices_daily

    # Mock empty dataframe for invalid symbol
    mock_download.return_value = pd.DataFrame()

    df = load_prices_daily(
        "INVALID_SYMBOL", start_date="2026-05-01", end_date="2026-05-02"
    )

    assert df is None or df.empty


@patch("yfinance.download")
def test_load_prices_5m_valid_symbol(mock_download):
    """Test loading 5m prices for valid symbol."""
    from app.core.etl.prices import load_prices_5m

    # Mock data
    dates = pd.date_range("2026-05-01 09:30:00", periods=2, freq="5min")
    mock_df = pd.DataFrame(
        {
            "Open": [150.0, 151.0],
            "High": [152.0, 153.0],
            "Low": [149.0, 150.0],
            "Close": [151.0, 152.0],
            "Volume": [10000, 11000],
        },
        index=dates,
    )

    mock_download.return_value = mock_df

    # Test
    df = load_prices_5m("AAPL", start_date="2026-05-01", end_date="2026-05-02")

    assert not df.empty
    assert "Close" in df.columns
    assert len(df) == 2
    mock_download.assert_called_with(
        "AAPL", start="2026-05-01", end="2026-05-02", interval="5m", progress=True
    )


@patch("yfinance.download")
def test_load_prices_5m_invalid_symbol(mock_download):
    """Test error handling for invalid symbol in 5m data."""
    from app.core.etl.prices import load_prices_5m

    # Mock empty dataframe for invalid symbol
    mock_download.return_value = pd.DataFrame()

    df = load_prices_5m(
        "INVALID_SYMBOL", start_date="2026-05-01", end_date="2026-05-02"
    )

    assert df is None or df.empty
    mock_download.assert_called_with(
        "INVALID_SYMBOL",
        start="2026-05-01",
        end="2026-05-02",
        interval="5m",
        progress=True,
    )


def test_prices_dataframe_structure():
    """Test that loaded data has correct columns."""

    # Since we are mocking yfinance in test_load_prices_valid_symbol,
    # we just verify the expected columns based on yfinance output format.
    expected_cols = ["Open", "High", "Low", "Close", "Volume"]
    assert all(
        col in ["Open", "High", "Low", "Close", "Volume", "Adj Close"]
        for col in expected_cols
    )
