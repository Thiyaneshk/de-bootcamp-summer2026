"""
Phase 1: Stock Overview

Real-time stock data viewer with charts.

TODO: Implement:
- Symbol selector
- Date range picker
- Load data from yfinance
- Display OHLCV data
- Plotly candlestick chart
"""

from datetime import date, timedelta

import plotly.graph_objects as go
import streamlit as st

from app.core.etl.prices import load_prices_daily


@st.cache_data(ttl=300)
def cached_load(symbol: str, start_date: str | None, end_date: str | None):
    return load_prices_daily(symbol, start_date=start_date, end_date=end_date)


def main():
    """Stock overview page."""
    st.title("📈 Stock Overview")
    col1, col2 = st.columns([3, 1])

    with col1:
        symbol = st.text_input(
            "Symbol",
            value="AAPL",
            help="Enter a stock ticker symbol (e.g., AAPL, MSFT, BTC-USD)",
        )
        today = date.today()
        default_start = today - timedelta(days=365)
        date_range = st.date_input(
            "Date range",
            value=(default_start, today),
            help="Select the start and end dates for the historical data",
        )

    with col2:
        st.write("\n")
        st.write("\n")  # Add a bit more spacing to align with inputs
        if st.button("Load Data", type="primary", use_container_width=True):
            start_iso = (
                date_range[0].isoformat()
                if isinstance(date_range, tuple)
                else date_range.isoformat()
            )
            end_iso = (
                (date_range[1] + timedelta(days=1)).isoformat()
                if isinstance(date_range, tuple)
                else (date_range + timedelta(days=1)).isoformat()
            )

            with st.spinner(f"Loading data for {symbol}..."):
                df = cached_load(symbol, start_iso, end_iso)

            if df is None or df.empty:
                st.warning(f"No data returned for {symbol} in the selected date range.")
                return
            st.success(f"Successfully loaded {len(df):,} rows")
            st.dataframe(df.tail(100))

            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=df.index,
                        open=df["Open"],
                        high=df["High"],
                        low=df["Low"],
                        close=df["Close"],
                        name=symbol,
                    )
                ]
            )
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=600)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(
                "👆 Set a symbol and date range, then click **Load Data** to view the chart"
            )


if __name__ == "__main__":
    main()
