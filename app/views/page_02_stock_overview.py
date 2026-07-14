"""
Phase 1: Stock Overview

Real-time stock data viewer with charts.
"""

from datetime import date, timedelta

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from app.core.etl.prices import load_prices_daily


@st.cache_data(ttl=300)
def cached_load(symbol: str, start_date: str | None, end_date: str | None):
    return load_prices_daily(symbol, start_date=start_date, end_date=end_date)


def main():
    """Stock overview page."""

    # ── Header banner (consistent with other pages) ──────────────────────────
    st.markdown(
        """
        <div style="
            background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);
            border:1px solid #334155;border-radius:14px;
            padding:22px 24px 16px;margin-bottom:20px
        ">
            <h2 style="margin:0;color:#e2e8f0">📈 Stock Overview</h2>
            <p style="color:#94a3b8;margin:6px 0 0;font-size:0.92rem">
                Load daily OHLCV data from Yahoo Finance · Interactive candlestick charts with volume
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Controls row ─────────────────────────────────────────────────────────
    col_sym, col_dates, col_btn = st.columns([2, 4, 1])

    with col_sym:
        symbol = st.text_input(
            "Symbol",
            value="AAPL",
            help="Enter a stock ticker symbol (e.g., AAPL, MSFT, BTC-USD)",
        )

    with col_dates:
        today = date.today()
        default_start = today - timedelta(days=365)
        date_range = st.date_input(
            "Date range",
            value=(default_start, today),
            help="Select the start and end dates for the historical data",
        )

    with col_btn:
        st.write("")  # spacing to align button with inputs
        load_clicked = st.button("Load Data", type="primary", use_container_width=True)

    # ── Load and display ─────────────────────────────────────────────────────
    if load_clicked:
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

        st.success(f"Successfully loaded {len(df):,} rows for **{symbol}**")

        # ── KPI cards ────────────────────────────────────────────────────────
        latest = df.iloc[-1]
        earliest = df.iloc[0]
        price_change = latest["Close"] - earliest["Close"]
        pct_change = (price_change / earliest["Close"]) * 100 if earliest["Close"] else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Latest Close", f"${latest['Close']:.2f}")
        k2.metric(
            "Period Change",
            f"{pct_change:+.2f}%",
            delta=f"${price_change:+.2f}",
        )
        k3.metric("Period High", f"${df['High'].max():.2f}")
        k4.metric("Period Low", f"${df['Low'].min():.2f}")

        # ── Candlestick chart with volume subplot ────────────────────────────
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.75, 0.25],
            subplot_titles=[f"{symbol} Price", "Volume"],
        )

        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="Price",
                increasing_line_color="#10b981",
                decreasing_line_color="#ef4444",
            ),
            row=1,
            col=1,
        )

        # Volume bars colored by price direction
        colors = [
            "#10b981" if c >= o else "#ef4444"
            for c, o in zip(df["Close"], df["Open"])
        ]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name="Volume",
                marker_color=colors,
                opacity=0.6,
            ),
            row=2,
            col=1,
        )

        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            paper_bgcolor="rgba(15, 23, 42, 1)",
            margin=dict(l=20, r=20, t=40, b=20),
            height=650,
            showlegend=False,
            xaxis_rangeslider_visible=False,
            xaxis=dict(showgrid=True, gridcolor="#334155"),
            xaxis2=dict(showgrid=True, gridcolor="#334155"),
            yaxis=dict(showgrid=True, gridcolor="#334155"),
            yaxis2=dict(showgrid=True, gridcolor="#334155"),
        )

        st.plotly_chart(fig, use_container_width=True)

        # ── Data table ───────────────────────────────────────────────────────
        with st.expander(f"📋 Raw Data Table ({len(df):,} rows)", expanded=False):
            st.dataframe(df.tail(100), use_container_width=True)
    else:
        st.info(
            "👆 Set a symbol and date range, then click **Load Data** to view the chart"
        )


if __name__ == "__main__":
    main()
