"""
Phase 4: Analytics & Insights

Advanced analytics, comparative charts, volatility metrics, volume spikes,
and daily return correlation heatmaps.
"""

import logging
from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text

from app.db.connection import get_postgres_engine

logger = logging.getLogger(__name__)


@st.cache_data(ttl=30)
def load_analysis_symbols() -> list[str]:
    """Load distinct symbols from public_marts.fct_daily_prices."""
    try:
        query = (
            "SELECT DISTINCT symbol FROM public_marts.fct_daily_prices ORDER BY symbol"
        )
        with get_postgres_engine() as engine:
            with engine.connect() as conn:
                result = conn.execute(text(query)).fetchall()
                return [r[0] for r in result]
    except Exception as e:
        logger.warning("Failed to load symbols from fct_daily_prices: %s", e)
        # Fallback list if table does not exist
        return []


@st.cache_data(ttl=30)
def load_daily_prices(symbols: list[str]) -> pd.DataFrame:
    """Load daily prices from PostgreSQL for the given list of symbols."""
    if not symbols:
        return pd.DataFrame()
    try:
        query = """
            SELECT
                symbol,
                date,
                daily_open,
                daily_high,
                daily_low,
                daily_close,
                daily_volume
            FROM public_marts.fct_daily_prices
            WHERE symbol = ANY(:symbols)
            ORDER BY symbol, date ASC
        """
        with get_postgres_engine() as engine:
            df = pd.read_sql(text(query), engine, params={"symbols": list(symbols)})
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        return df
    except Exception as e:
        logger.error("Failed to load daily prices for %s: %s", symbols, e)
        return pd.DataFrame()


def main():
    """Analytics page."""

    st.markdown(
        """
        <div style="
            background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);
            border:1px solid #334155;border-radius:14px;
            padding:22px 24px 16px;margin-bottom:20px
        ">
            <h2 style="margin:0;color:#e2e8f0">📉 Analytics & Insights</h2>
            <p style="color:#94a3b8;margin:6px 0 0;font-size:0.92rem">
                Compare multi-symbol cumulative returns · Volatility profiles · Volume spike alerts · Daily return correlation
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    all_symbols = load_analysis_symbols()

    if not all_symbols:
        st.warning(
            "⚠️ No daily price data found in PostgreSQL. "
            "Please ensure the Airflow DAG has run successfully and populated `public_marts.fct_daily_prices`.\n\n"
            "**Steps to fix:**\n"
            "1. Access the Airflow UI at http://localhost:8080 and trigger the `etl_prices_dag` DAG.\n"
            "2. Or, run dbt manually in your terminal:\n"
            "```bash\n"
            "cd dbt && uv run dbt run --target prod\n"
            "```"
        )
        return

    # Filter selections
    col_sym, col_start, col_end = st.columns([3, 2, 2])

    with col_sym:
        selected_symbols = st.multiselect(
            "Select Symbols",
            options=all_symbols,
            default=all_symbols[:3] if len(all_symbols) >= 3 else all_symbols,
            help="Select one or more symbols to analyze and compare",
        )

    with col_start:
        start_date = st.date_input(
            "Start Date",
            value=date.today() - timedelta(days=90),
            help="Show data starting from this date",
        )

    with col_end:
        end_date = st.date_input(
            "End Date", value=date.today(), help="Show data ending on this date"
        )

    if not selected_symbols:
        st.info("👆 Please select at least one symbol to load the analysis.")
        return

    if start_date > end_date:
        st.error("Error: Start date must be before or equal to End date.")
        return

    # Load data
    with st.spinner("Analyzing market data..."):
        raw_df = load_daily_prices(selected_symbols)

    if raw_df.empty:
        st.warning("No price data returned from PostgreSQL database.")
        return

    # Apply date filters
    df = raw_df[
        (raw_df["date"].dt.date >= start_date) & (raw_df["date"].dt.date <= end_date)
    ].copy()

    if df.empty:
        st.warning(
            f"No records available for the selected symbols in date range {start_date} to {end_date}."
        )
        return

    # Compute daily return for return calculations
    df["daily_return"] = df.groupby("symbol")["daily_close"].pct_change()
    df["cumulative_return"] = df.groupby("symbol")["daily_close"].transform(
        lambda x: (x / x.iloc[0] - 1) * 100 if len(x) > 0 else 0
    )

    # Primary symbol statistics (KPI Cards)
    primary_symbol = selected_symbols[0]
    df_primary = df[df["symbol"] == primary_symbol].sort_values("date")

    st.markdown(f"### 🎯 Primary Symbol: **{primary_symbol}** Key Stats")

    if not df_primary.empty:
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

        latest_row = df_primary.iloc[-1]
        earliest_row = df_primary.iloc[0]

        # Current Price
        kpi_col1.metric(
            label=f"{primary_symbol} Price", value=f"{latest_row['daily_close']:.2f}"
        )

        # 7-day change
        target_7d = latest_row["date"] - timedelta(days=7)
        df_7d = df_primary[df_primary["date"] <= target_7d]
        if not df_7d.empty:
            price_7d = df_7d.iloc[-1]["daily_close"]
            perf_7d = ((latest_row["daily_close"] - price_7d) / price_7d) * 100
            kpi_col2.metric(
                label="7-Day Performance",
                value=f"{perf_7d:+.2f}%",
                delta=f"{latest_row['daily_close'] - price_7d:.2f}",
            )
        else:
            # Fallback to total period change
            perf_period = (
                (latest_row["daily_close"] - earliest_row["daily_close"])
                / earliest_row["daily_close"]
            ) * 100
            kpi_col2.metric(
                label="Period Performance",
                value=f"{perf_period:+.2f}%",
                delta=f"{latest_row['daily_close'] - earliest_row['daily_close']:.2f}",
            )

        # 30-day (or period) High/Low
        high_30d = df_primary["daily_high"].max()
        low_30d = df_primary["daily_low"].min()
        kpi_col3.metric(
            label="Period Range (High / Low)", value=f"{high_30d:.2f} / {low_30d:.2f}"
        )

        # Average volume
        avg_vol = df_primary["daily_volume"].mean()
        kpi_col4.metric(label="Avg Daily Volume", value=f"{int(avg_vol):,}")
    else:
        st.info("Primary symbol data unavailable.")

    st.divider()

    # ── Tabs: Charts ──────────────────────────────────────────────────────────
    tab_perf, tab_vol, tab_vol_spikes, tab_corr = st.tabs(
        [
            "📈 Performance Comparison",
            "⚡ Volatility Profile",
            "⚠️ Volume Spike Alerts",
            "🧮 Correlation Heatmap",
        ]
    )

    # TAB 1: Performance Comparison
    with tab_perf:
        st.markdown("#### Cumulative Returns Comparison")
        st.markdown(
            "This chart compares the cumulative return (%) of the selected stocks starting from the baseline "
            f"on **{start_date}** (initial close price is normalized to 0%)."
        )

        fig_perf = go.Figure()
        for sym in selected_symbols:
            df_sym = df[df["symbol"] == sym].sort_values("date")
            if df_sym.empty:
                continue
            fig_perf.add_trace(
                go.Scatter(
                    x=df_sym["date"],
                    y=df_sym["cumulative_return"],
                    mode="lines",
                    name=sym,
                    line=dict(width=2.2),
                    hovertemplate=f"<b>{sym}</b>: %{{y:+.2f}}%<extra></extra>",
                )
            )

        fig_perf.update_layout(
            template="plotly_dark",
            hovermode="x unified",
            xaxis_title="Date",
            yaxis_title="Cumulative Return (%)",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            paper_bgcolor="rgba(15, 23, 42, 1)",
            margin=dict(l=20, r=20, t=30, b=20),
            height=450,
            xaxis=dict(showgrid=True, gridcolor="#334155"),
            yaxis=dict(showgrid=True, gridcolor="#334155"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(15, 23, 42, 0.5)",
            ),
        )
        st.plotly_chart(fig_perf, use_container_width=True)

    # TAB 2: Volatility Profile
    with tab_vol:
        st.markdown("#### Volatility Metrics & Rolling Risk")

        v_col1, v_col2 = st.columns([1, 2])

        # Calculate daily and annualized volatility per symbol
        vol_data = []
        for sym in selected_symbols:
            df_sym = df[df["symbol"] == sym]
            if df_sym.empty or len(df_sym) < 2:
                continue
            daily_vol = df_sym["daily_return"].std() * 100
            ann_vol = daily_vol * np.sqrt(252)
            vol_data.append(
                {
                    "Symbol": sym,
                    "Daily Volatility (%)": round(daily_vol, 3),
                    "Annualized Volatility (%)": round(ann_vol, 2),
                }
            )

        vol_df = pd.DataFrame(vol_data)

        with v_col1:
            st.markdown("**Volatility Comparison**")
            if not vol_df.empty:
                st.dataframe(vol_df.set_index("Symbol"), use_container_width=True)

                # Volatility Bar Chart
                fig_vol = px.bar(
                    vol_df,
                    x="Symbol",
                    y="Annualized Volatility (%)",
                    color="Symbol",
                    title="Annualized Volatility comparison",
                    template="plotly_dark",
                )
                fig_vol.update_layout(
                    plot_bgcolor="rgba(15, 23, 42, 0.4)",
                    paper_bgcolor="rgba(15, 23, 42, 1)",
                    showlegend=False,
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                )
                st.plotly_chart(fig_vol, use_container_width=True)
            else:
                st.info("Not enough data to calculate volatility.")

        with v_col2:
            st.markdown("**20-Day Rolling Volatility Trend (Annualized)**")

            fig_roll = go.Figure()
            for sym in selected_symbols:
                df_sym = df[df["symbol"] == sym].sort_values("date").copy()
                if df_sym.empty or len(df_sym) < 20:
                    continue
                # Rolling std * 100 * sqrt(252)
                df_sym["rolling_vol"] = (
                    df_sym["daily_return"].rolling(20).std() * 100 * np.sqrt(252)
                )
                df_sym = df_sym.dropna(subset=["rolling_vol"])

                fig_roll.add_trace(
                    go.Scatter(
                        x=df_sym["date"],
                        y=df_sym["rolling_vol"],
                        mode="lines",
                        name=sym,
                        line=dict(width=2),
                        hovertemplate=f"<b>{sym} Rolling Vol</b>: %{{y:.2f}}%<extra></extra>",
                    )
                )

            fig_roll.update_layout(
                template="plotly_dark",
                hovermode="x unified",
                xaxis_title="Date",
                yaxis_title="Rolling Volatility (%)",
                plot_bgcolor="rgba(15, 23, 42, 0.4)",
                paper_bgcolor="rgba(15, 23, 42, 1)",
                margin=dict(l=20, r=20, t=30, b=20),
                height=400,
                xaxis=dict(showgrid=True, gridcolor="#334155"),
                yaxis=dict(showgrid=True, gridcolor="#334155"),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor="rgba(15, 23, 42, 0.5)",
                ),
            )
            st.plotly_chart(fig_roll, use_container_width=True)

    # TAB 3: Volume Spike Alerts
    with tab_vol_spikes:
        st.markdown("#### Unusual Trading Volume Spikes")
        st.markdown(
            "Volume spikes often accompany major news, earnings releases, or trend breakouts. "
            "Below are dates where the daily trading volume exceeded **2 standard deviations** "
            "above the symbol's rolling average."
        )

        all_spikes = []
        for sym in selected_symbols:
            df_sym = df[df["symbol"] == sym].sort_values("date").copy()
            if df_sym.empty or len(df_sym) < 10:
                continue

            mean_vol = df_sym["daily_volume"].mean()
            std_vol = df_sym["daily_volume"].std()
            threshold = mean_vol + 2 * std_vol

            spikes = df_sym[df_sym["daily_volume"] > threshold]

            for _, r in spikes.iterrows():
                ratio = r["daily_volume"] / mean_vol
                all_spikes.append(
                    {
                        "date": r["date"].strftime("%Y-%m-%d"),
                        "timestamp": r["date"],
                        "symbol": sym,
                        "volume": r["daily_volume"],
                        "avg_volume": mean_vol,
                        "ratio": ratio,
                        "desc": f"Volume spike of <b>{int(r['daily_volume']):,}</b> shares (<b>{ratio:.1f}x</b> the period average of {int(mean_vol):,})",
                    }
                )

        all_spikes = sorted(all_spikes, key=lambda x: x["timestamp"], reverse=True)

        if not all_spikes:
            st.info("No unusual volume spikes detected in the selected time range.")
        else:
            for spike in all_spikes[:12]:
                st.markdown(
                    f"📅 **{spike['date']}** · **{spike['symbol']}** · {spike['desc']}",
                    unsafe_allow_html=True,
                )

        # Interactive Volume Trend Chart
        st.markdown("---")
        st.markdown("**Volume History Over Time**")
        fig_vol_hist = go.Figure()
        for sym in selected_symbols:
            df_sym = df[df["symbol"] == sym].sort_values("date")
            if df_sym.empty:
                continue
            fig_vol_hist.add_trace(
                go.Bar(
                    x=df_sym["date"],
                    y=df_sym["daily_volume"],
                    name=sym,
                    hovertemplate=f"<b>{sym} Volume</b>: %{{y:,}}<extra></extra>",
                )
            )

        fig_vol_hist.update_layout(
            template="plotly_dark",
            barmode="group",
            xaxis_title="Date",
            yaxis_title="Volume",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            paper_bgcolor="rgba(15, 23, 42, 1)",
            margin=dict(l=20, r=20, t=30, b=20),
            height=350,
            xaxis=dict(showgrid=True, gridcolor="#334155"),
            yaxis=dict(showgrid=True, gridcolor="#334155"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor="rgba(15, 23, 42, 0.5)",
            ),
        )
        st.plotly_chart(fig_vol_hist, use_container_width=True)

    # TAB 4: Correlation Heatmap
    with tab_corr:
        st.markdown("#### Cross-Symbol Daily Returns Correlation Matrix")

        if len(selected_symbols) < 2:
            st.warning(
                "⚠️ Please select 2 or more symbols to display the correlation heatmap."
            )
        else:
            # Pivot to get returns per symbol per date
            pivot_df = df.pivot(index="date", columns="symbol", values="daily_return")

            # Compute correlation matrix
            corr_matrix = pivot_df.corr().round(4)

            # Plotly Heatmap
            fig_heat = px.imshow(
                corr_matrix,
                text_auto=".3f",
                aspect="auto",
                color_continuous_scale="RdBu",
                color_continuous_midpoint=0,
                labels=dict(color="Correlation"),
                template="plotly_dark",
            )

            fig_heat.update_layout(
                title=dict(
                    text="Correlation of Daily Returns", x=0.5, xanchor="center"
                ),
                plot_bgcolor="rgba(15, 23, 42, 0.4)",
                paper_bgcolor="rgba(15, 23, 42, 1)",
                margin=dict(l=40, r=40, t=60, b=40),
                height=450,
            )

            st.plotly_chart(fig_heat, use_container_width=True)


if __name__ == "__main__":
    main()
