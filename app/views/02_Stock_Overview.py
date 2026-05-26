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

import streamlit as st
import plotly.graph_objects as go
from datetime import date, timedelta
import pandas as pd

from app.core.etl.prices import load_prices_daily
from app.core.indices import get_index_symbols
from app.db.connection import get_db_engine
from app.db.utils import insert_prices


@st.cache_data(ttl=300)
def cached_load(symbol: str, start_date: str | None, end_date: str | None):
    return load_prices_daily(symbol, start_date=start_date, end_date=end_date)


def df_to_price_records(df: pd.DataFrame, symbol: str) -> list[dict]:
    """Convert DataFrame to list of price records for database insertion."""
    records = []
    for timestamp, row in df.iterrows():
        records.append({
            'symbol': symbol,
            'timestamp': timestamp,
            'open': row.get('Open'),
            'high': row.get('High'),
            'low': row.get('Low'),
            'close': row.get('Close'),
            'volume': row.get('Volume')
        })
    return records


def main():
    """Stock overview page."""
    st.title("📈 Stock Overview")
    
    st.write("Load stock data from an index and view price data with candlestick charts.")
    
    # Session state for managing loaded data
    if 'loaded_stocks' not in st.session_state:
        st.session_state.loaded_stocks = {}
    
    # Create layout
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        index_name = st.selectbox(
            "Index-Constituent",
            options=["Nifty50", "BankNifty"],
            help="Select the index to load stocks from"
        )
    
    with col2:
        today = date.today()
        default_start = today - timedelta(days=365)
        date_range = st.date_input(
            "Date range",
            value=(default_start, today),
            max_value=today
        )
    
    with col3:
        st.write("\n")
        load_button = st.button("Load", use_container_width=True)
    
    st.divider()
    
    if load_button:
        # Get stocks for selected index
        index_key = index_name.lower()
        symbols = get_index_symbols(index_key)
        
        if not symbols:
            st.error(f"No symbols found for {index_name}")
            return
        
        st.info(f"Loading {len(symbols)} stocks from {index_name}...")
        
        # Prepare date strings
        start_iso = date_range[0].isoformat() if isinstance(date_range, tuple) else date_range.isoformat()
        end_iso = (date_range[1] + timedelta(days=1)).isoformat() if isinstance(date_range, tuple) else (date_range + timedelta(days=1)).isoformat()
        
        # Load data for all symbols
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        loaded_data = {}
        failed_symbols = []
        
        for idx, symbol in enumerate(symbols):
            status_text.text(f"Loading {symbol} ({idx + 1}/{len(symbols)})...")
            progress_bar.progress((idx + 1) / len(symbols))
            
            try:
                df = cached_load(symbol, start_iso, end_iso)
                
                if df is None or df.empty:
                    failed_symbols.append(symbol)
                    continue
                
                loaded_data[symbol] = df
                
                # Store in database
                try:
                    with get_db_engine() as engine:
                        records = df_to_price_records(df, symbol)
                        inserted = insert_prices(engine, records)
                        st.session_state.loaded_stocks[symbol] = df
                except Exception as db_err:
                    st.warning(f"Could not save {symbol} to database: {db_err}")
                    st.session_state.loaded_stocks[symbol] = df
                    
            except Exception as e:
                st.warning(f"Error loading {symbol}: {e}")
                failed_symbols.append(symbol)
        
        progress_bar.empty()
        status_text.empty()
        
        # Summary
        success_count = len(loaded_data)
        if success_count > 0:
            st.success(f"✅ Successfully loaded {success_count} stocks")
        if failed_symbols:
            st.warning(f"⚠️ Failed to load {len(failed_symbols)} stocks: {', '.join(failed_symbols[:5])}")
    
    # Display loaded stocks
    if st.session_state.loaded_stocks:
        st.subheader(f"Loaded Stocks ({len(st.session_state.loaded_stocks)})")
        
        # Create tabs for each stock (show first 10)
        stocks_to_display = list(st.session_state.loaded_stocks.items())[:10]
        
        if len(st.session_state.loaded_stocks) > 10:
            st.info(f"Showing first 10 of {len(st.session_state.loaded_stocks)} loaded stocks")
        
        for symbol, df in stocks_to_display:
            with st.expander(f"📊 {symbol}"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Close", f"${df['Close'].iloc[-1]:.2f}")
                with col2:
                    change = df['Close'].iloc[-1] - df['Open'].iloc[-1]
                    st.metric("Change", f"${change:.2f}")
                with col3:
                    st.metric("High", f"${df['High'].max():.2f}")
                with col4:
                    st.metric("Low", f"${df['Low'].min():.2f}")
                
                # Candlestick chart
                fig = go.Figure(data=[
                    go.Candlestick(
                        x=df.index,
                        open=df["Open"],
                        high=df["High"],
                        low=df["Low"],
                        close=df["Close"],
                        name=symbol,
                    )
                ])
                fig.update_layout(
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=400,
                    title=f"{symbol} Price Chart"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                st.dataframe(
                    df.tail(10),
                    use_container_width=True,
                    column_config={
                        "Open": st.column_config.NumberColumn(format="%.2f"),
                        "High": st.column_config.NumberColumn(format="%.2f"),
                        "Low": st.column_config.NumberColumn(format="%.2f"),
                        "Close": st.column_config.NumberColumn(format="%.2f"),
                        "Volume": st.column_config.NumberColumn(format="%.0f"),
                    }
                )
    else:
        st.info("Click 'Load' to fetch stock data for the selected index")
    

if __name__ == "__main__":
    main()
