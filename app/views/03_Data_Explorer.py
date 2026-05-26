"""
Phase 1: Data Explorer

Raw data table viewer and query interface.

TODO: Implement:
- Symbol and date range filters
- Display raw price data in table
- Data export (CSV)
- Basic statistics
"""

import streamlit as st
import pandas as pd
from app.db.connection import get_db_engine
from app.db.utils import get_available_symbols, get_symbol_data_as_dataframe


@st.cache_data(ttl=300)
def fetch_available_symbols():
    """Fetch list of available symbols from database."""
    try:
        with get_db_engine() as engine:
            symbols = get_available_symbols(engine)
            return symbols if symbols else []
    except Exception as e:
        st.error(f"Error fetching symbols: {e}")
        return []


def main():
    """Data explorer page."""
    st.title("🔍 Data Explorer")
    
    st.write("Browse and explore raw stock price data stored in the database.")
    
    # Get available symbols
    available_symbols = fetch_available_symbols()
    
    if not available_symbols:
        st.info("📊 No data available yet. Please load data first using the Stock Overview page.")
        return
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_symbol = st.selectbox(
            "Select Stock Ticker",
            options=available_symbols,
            help="Choose a stock ticker to view available data"
        )
    
    with col2:
        num_rows = st.number_input(
            "Number of rows",
            min_value=1,
            max_value=100,
            value=5,
            help="Number of most recent rows to display"
        )
    
    if selected_symbol:
        st.divider()
        
        # Fetch data for selected symbol
        try:
            with get_db_engine() as engine:
                df = get_symbol_data_as_dataframe(engine, selected_symbol, limit=num_rows)
            
            if df.empty:
                st.warning(f"No data found for {selected_symbol}")
            else:
                # Display summary statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Rows in Database", len(df))
                with col2:
                    if "timestamp" in df.columns:
                        st.metric("Latest Date", df["timestamp"].max() if len(df) > 0 else "N/A")
                with col3:
                    if "timestamp" in df.columns:
                        st.metric("Earliest Date", df["timestamp"].min() if len(df) > 0 else "N/A")
                
                st.subheader(f"Data for {selected_symbol}")
                
                # Display data table with better formatting
                display_df = df.copy()
                if "timestamp" in display_df.columns:
                    display_df = display_df.sort_values("timestamp", ascending=True)
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "timestamp": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD HH:mm"),
                        "open": st.column_config.NumberColumn("Open", format="%.2f"),
                        "high": st.column_config.NumberColumn("High", format="%.2f"),
                        "low": st.column_config.NumberColumn("Low", format="%.2f"),
                        "close": st.column_config.NumberColumn("Close", format="%.2f"),
                        "volume": st.column_config.NumberColumn("Volume", format="%.0f"),
                    }
                )
                
                # Summary statistics
                st.subheader("Price Statistics")
                if all(col in display_df.columns for col in ["open", "high", "low", "close"]):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Min Close", f"${display_df['close'].min():.2f}")
                    with col2:
                        st.metric("Max Close", f"${display_df['close'].max():.2f}")
                    with col3:
                        st.metric("Avg Close", f"${display_df['close'].mean():.2f}")
                    with col4:
                        st.metric("Avg Volume", f"{display_df['volume'].mean():,.0f}")
                
                # Export option
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv_data,
                    file_name=f"{selected_symbol}_data.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Error loading data: {e}")
    

if __name__ == "__main__":
    main()
