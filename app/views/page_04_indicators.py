"""
Phase 3 / Phase 4: Technical Indicators

Display dbt-generated technical indicators (SMA 20, SMA 50, EMA 50, EMA 200)
from the PostgreSQL database.
"""

import io
import logging
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text

from app.db.connection import get_postgres_engine

logger = logging.getLogger(__name__)


@st.cache_data(ttl=30)
def load_indicators_symbols() -> list[str]:
    """Load distinct symbols from public_marts.fct_technical_indicators."""
    try:
        query = "SELECT DISTINCT symbol FROM public_marts.fct_technical_indicators ORDER BY symbol"
        with get_postgres_engine() as engine:
            with engine.connect() as conn:
                result = conn.execute(text(query)).fetchall()
                return [r[0] for r in result]
    except Exception as e:
        logger.warning("Failed to load symbols from fct_technical_indicators: %s", e)
        return []


@st.cache_data(ttl=30)
def load_indicator_data(symbol: str) -> pd.DataFrame:
    """Load indicators data for a symbol from PostgreSQL."""
    try:
        query = """
            SELECT
                timestamp,
                close,
                sma_20,
                sma_50,
                ema_50,
                ema_200
            FROM public_marts.fct_technical_indicators
            WHERE symbol = :symbol
            ORDER BY timestamp ASC
        """
        with get_postgres_engine() as engine:
            df = pd.read_sql(text(query), engine, params={"symbol": symbol})
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception as e:
        logger.error("Failed to load indicator data for %s: %s", symbol, e)
        return pd.DataFrame()


def detect_crossovers(df: pd.DataFrame) -> list[dict]:
    """Detect SMA and EMA crossover events in the dataset."""
    events = []
    if len(df) < 2:
        return events

    # SMA 20 vs SMA 50
    df = df.copy()
    df["sma_diff"] = df["sma_20"] - df["sma_50"]
    df["sma_diff_prev"] = df["sma_diff"].shift(1)

    # EMA 50 vs EMA 200
    df["ema_diff"] = df["ema_50"] - df["ema_200"]
    df["ema_diff_prev"] = df["ema_diff"].shift(1)

    for i in range(1, len(df)):
        row = df.iloc[i]
        date_str = row["timestamp"].strftime("%Y-%m-%d")

        # SMA Golden / Death Cross
        if pd.notna(row["sma_diff"]) and pd.notna(row["sma_diff_prev"]):
            if row["sma_diff"] > 0 >= row["sma_diff_prev"]:
                events.append({
                    "date": date_str,
                    "timestamp": row["timestamp"],
                    "type": "Golden Cross (SMA 20/50)",
                    "desc": f"SMA 20 crossed above SMA 50 at {row['close']:.2f}",
                    "is_bullish": True
                })
            elif row["sma_diff"] < 0 <= row["sma_diff_prev"]:
                events.append({
                    "date": date_str,
                    "timestamp": row["timestamp"],
                    "type": "Death Cross (SMA 20/50)",
                    "desc": f"SMA 20 crossed below SMA 50 at {row['close']:.2f}",
                    "is_bullish": False
                })

        # EMA Golden / Death Cross
        if pd.notna(row["ema_diff"]) and pd.notna(row["ema_diff_prev"]):
            if row["ema_diff"] > 0 >= row["ema_diff_prev"]:
                events.append({
                    "date": date_str,
                    "timestamp": row["timestamp"],
                    "type": "Golden Cross (EMA 50/200)",
                    "desc": f"EMA 50 crossed above EMA 200 at {row['close']:.2f}",
                    "is_bullish": True
                })
            elif row["ema_diff"] < 0 <= row["ema_diff_prev"]:
                events.append({
                    "date": date_str,
                    "timestamp": row["timestamp"],
                    "type": "Death Cross (EMA 50/200)",
                    "desc": f"EMA 50 crossed below EMA 200 at {row['close']:.2f}",
                    "is_bullish": False
                })

    return sorted(events, key=lambda x: x["timestamp"], reverse=True)


def main():
    """Technical indicators page."""

    st.markdown(
        """
        <div style="
            background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);
            border:1px solid #334155;border-radius:14px;
            padding:22px 24px 16px;margin-bottom:20px
        ">
            <h2 style="margin:0;color:#e2e8f0">📊 Technical Indicators</h2>
            <p style="color:#94a3b8;margin:6px 0 0;font-size:0.92rem">
                Inspect dbt-calculated moving averages (SMA 20/50, EMA 50/200) · Detect crossover signals
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    symbols = load_indicators_symbols()

    if not symbols:
        st.warning(
            "⚠️ No technical indicators data found in PostgreSQL. "
            "Please ensure the Airflow DAG has run successfully and populated `public_marts.fct_technical_indicators`.\n\n"
            "**Steps to fix:**\n"
            "1. Access the Airflow UI at http://localhost:8080 and trigger the `etl_prices_dag` DAG.\n"
            "2. Or, run dbt manually in your terminal:\n"
            "```bash\n"
            "cd dbt && uv run dbt run --target prod\n"
            "```"
        )
        return

    # Sidebar / filters layout
    col_sym, col_start, col_end = st.columns([2, 2, 2])

    with col_sym:
        selected_symbol = st.selectbox(
            "Select Symbol",
            options=symbols,
            index=0,
            help="Choose a symbol to analyze"
        )

    with col_start:
        start_date = st.date_input(
            "Start Date",
            value=date.today() - timedelta(days=90),
            help="Show data starting from this date"
        )

    with col_end:
        end_date = st.date_input(
            "End Date",
            value=date.today(),
            help="Show data ending on this date"
        )

    if start_date > end_date:
        st.error("Error: Start date must be before or equal to End date.")
        return

    # Load data
    with st.spinner(f"Loading indicators for {selected_symbol}..."):
        raw_df = load_indicator_data(selected_symbol)

    if raw_df.empty:
        st.warning(f"No records found for symbol {selected_symbol} in database.")
        return

    # Filter data by date range
    df = raw_df[(raw_df["timestamp"].dt.date >= start_date) & (raw_df["timestamp"].dt.date <= end_date)].copy()

    if df.empty:
        st.warning(f"No data available for {selected_symbol} in the selected date range ({start_date} to {end_date}).")
        return

    latest_row = df.iloc[-1]

    # ── KPI Cards ────────────────────────────────────────────────────────────
    st.markdown("### 📈 Current Trend & Signals")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    # Close price
    kpi_col1.metric(
        label=f"{selected_symbol} Close",
        value=f"{latest_row['close']:.2f}"
    )

    # SMA Crossover status
    sma_diff = latest_row["sma_20"] - latest_row["sma_50"] if pd.notna(latest_row["sma_20"]) and pd.notna(latest_row["sma_50"]) else None
    if sma_diff is not None:
        sma_status = "🟢 Bullish" if sma_diff > 0 else "🔴 Bearish"
        kpi_col2.metric(
            label="SMA 20/50 Signal",
            value=sma_status,
            delta=f"Diff: {sma_diff:.2f}",
            delta_color="normal"
        )
    else:
        kpi_col2.metric(label="SMA 20/50 Signal", value="No Data")

    # EMA Crossover status
    ema_diff = latest_row["ema_50"] - latest_row["ema_200"] if pd.notna(latest_row["ema_50"]) and pd.notna(latest_row["ema_200"]) else None
    if ema_diff is not None:
        ema_status = "🟢 Bullish" if ema_diff > 0 else "🔴 Bearish"
        kpi_col3.metric(
            label="EMA 50/200 Signal",
            value=ema_status,
            delta=f"Diff: {ema_diff:.2f}",
            delta_color="normal"
        )
    else:
        kpi_col3.metric(label="EMA 50/200 Signal", value="No Data")

    # Position relative to EMA 200
    price_vs_ema200 = latest_row["close"] - latest_row["ema_200"] if pd.notna(latest_row["ema_200"]) else None
    if price_vs_ema200 is not None:
        pct_above = (price_vs_ema200 / latest_row["ema_200"]) * 100
        trend_status = "🟢 Bull Market" if price_vs_ema200 > 0 else "🔴 Bear Market"
        kpi_col4.metric(
            label="Long-Term Trend",
            value=trend_status,
            delta=f"{pct_above:.1f}% vs EMA200"
        )
    else:
        kpi_col4.metric(label="Long-Term Trend", value="No Data")

    st.divider()

    # ── Interactive Plotly Chart ─────────────────────────────────────────────
    st.markdown("### 📊 Interactive Technical Chart")

    # Toggle which indicators to draw
    indicators_to_plot = st.multiselect(
        "Indicators to Overlay",
        options=["SMA 20", "SMA 50", "EMA 50", "EMA 200"],
        default=["SMA 20", "EMA 50"],
        help="Select which calculated lines to plot on top of the Close price"
    )

    fig = go.Figure()

    # Add Close Price
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["close"],
        mode="lines",
        name="Close Price",
        line=dict(color="#38bdf8", width=2.5),
        hovertemplate="Close: %{y:.2f}"
    ))

    # Add Selected Indicators
    color_map = {
        "SMA 20": ("#f59e0b", "dash"),    # Amber
        "SMA 50": ("#ef4444", "dashdot"), # Rose
        "EMA 50": ("#10b981", "solid"),   # Emerald
        "EMA 200": ("#8b5cf6", "solid")   # Violet
    }

    col_mapping = {
        "SMA 20": "sma_20",
        "SMA 50": "sma_50",
        "EMA 50": "ema_50",
        "EMA 200": "ema_200"
    }

    for ind in indicators_to_plot:
        db_col = col_mapping[ind]
        color, style = color_map[ind]
        if db_col in df.columns and not df[db_col].isnull().all():
            fig.add_trace(go.Scatter(
                x=df["timestamp"],
                y=df[db_col],
                mode="lines",
                name=ind,
                line=dict(color=color, width=1.5, dash=style),
                hovertemplate=f"{ind}: %{{y:.2f}}"
            ))

    fig.update_layout(
        template="plotly_dark",
        hovermode="x unified",
        plot_bgcolor="rgba(15, 23, 42, 0.4)",
        paper_bgcolor="rgba(15, 23, 42, 1)",
        margin=dict(l=20, r=20, t=40, b=20),
        height=500,
        xaxis=dict(showgrid=True, gridcolor="#334155"),
        yaxis=dict(showgrid=True, gridcolor="#334155"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(15, 23, 42, 0.5)"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Tabs for Signals and Tables ──────────────────────────────────────────
    tab_signals, tab_data = st.tabs(["⚡ Crossover Signal History", "📋 Raw Data Table"])

    with tab_signals:
        st.markdown("#### Detected Moving Average Crossovers")
        st.markdown(
            "Crossovers are classic technical triggers. A **Golden Cross** occurs when a shorter-term moving average "
            "crosses above a longer-term one (Bullish). A **Death Cross** is the opposite (Bearish)."
        )

        crossover_events = detect_crossovers(df)
        if not crossover_events:
            st.info("No crossover events detected in the selected time range.")
        else:
            for ev in crossover_events[:15]: # Show top 15 events
                "success" if ev["is_bullish"] else "danger"
                st.markdown(
                    f"**{ev['date']}** · "
                    f"<span style='color:{'#10b981' if ev['is_bullish'] else '#ef4444'}; font-weight:bold;'>{ev['type']}</span> · "
                    f"{ev['desc']}",
                    unsafe_allow_html=True
                )

    with tab_data:
        st.markdown(f"#### Calculated Indicators for {selected_symbol}")

        # Display data frame
        disp_df = df.copy()
        disp_df["date"] = disp_df["timestamp"].dt.strftime("%Y-%m-%d")
        disp_df = disp_df[["date", "close", "sma_20", "sma_50", "ema_50", "ema_200"]]

        for col in ["close", "sma_20", "sma_50", "ema_50", "ema_200"]:
            disp_df[col] = disp_df[col].round(4)

        st.dataframe(disp_df.set_index("date"), use_container_width=True, height=300)

        # CSV download
        csv_buf = io.StringIO()
        disp_df.to_csv(csv_buf, index=False)
        st.download_button(
            label="⬇️ Download Indicators as CSV",
            data=csv_buf.getvalue(),
            file_name=f"{selected_symbol}_indicators_{date.today()}.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()
