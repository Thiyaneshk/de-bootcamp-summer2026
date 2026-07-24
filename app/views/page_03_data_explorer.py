"""
Phase 1 / Phase 2: Data Explorer

View raw price data stored in DuckDB, inspect statistics,
export to CSV, and push selected symbols to PostgreSQL.
"""

import io
import logging
import os
from datetime import date, timedelta

import duckdb
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# ── DuckDB helpers ────────────────────────────────────────────────────────────

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "data/app.duckdb")


def _duck_connect():
    """Open a read-only-safe DuckDB connection."""
    os.makedirs(os.path.dirname(DUCKDB_PATH) or "data", exist_ok=True)
    return duckdb.connect(DUCKDB_PATH)


def _table_exists(conn, table: str) -> bool:
    try:
        rows = conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name = ?",
            [table],
        ).fetchone()
        return rows[0] > 0
    except Exception:
        return False


@st.cache_data(ttl=30)
def load_symbols() -> list[str]:
    """Return all distinct symbols stored in DuckDB prices table."""
    try:
        conn = _duck_connect()
        if not _table_exists(conn, "prices"):
            conn.close()
            return []
        rows = conn.execute(
            "SELECT DISTINCT symbol FROM prices ORDER BY symbol"
        ).fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        logger.warning("Could not list symbols: %s", e)
        return []


@st.cache_data(ttl=30)
def load_db_stats() -> dict:
    """Return aggregate stats from DuckDB prices table."""
    try:
        conn = _duck_connect()
        if not _table_exists(conn, "prices"):
            conn.close()
            return {}
        r = conn.execute(
            "SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(timestamp), MAX(timestamp) FROM prices"
        ).fetchone()
        conn.close()
        size_mb = (
            round(os.path.getsize(DUCKDB_PATH) / 1_048_576, 2)
            if os.path.exists(DUCKDB_PATH)
            else 0
        )
        return {
            "total_rows": r[0],
            "symbols": r[1],
            "earliest": str(r[2])[:10] if r[2] else "—",
            "latest": str(r[3])[:10] if r[3] else "—",
            "size_mb": size_mb,
        }
    except Exception as e:
        logger.warning("Stats query failed: %s", e)
        return {}


def load_prices_from_duck(
    symbols: list[str],
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    """Load price rows from DuckDB for given symbols and date range."""
    if not symbols:
        return pd.DataFrame()
    try:
        conn = _duck_connect()
        if not _table_exists(conn, "prices"):
            conn.close()
            return pd.DataFrame()

        placeholders = ", ".join(["?"] * len(symbols))
        params: list = list(symbols)
        where_extra = ""
        if start:
            where_extra += " AND timestamp >= ?"
            params.append(str(start))
        if end:
            where_extra += " AND timestamp < ?"
            params.append(str(end + timedelta(days=1)))

        sql = f"""
            SELECT symbol, timestamp, open, high, low, close, volume
            FROM prices
            WHERE symbol IN ({placeholders}){where_extra}
            ORDER BY symbol, timestamp DESC
        """
        df = conn.execute(sql, params).df()
        conn.close()
        return df
    except Exception as e:
        st.error(f"DuckDB query error: {e}")
        return pd.DataFrame()


# ── PostgreSQL push ───────────────────────────────────────────────────────────


def push_to_postgres(df: pd.DataFrame, pg_url: str) -> tuple[int, str]:
    """
    Upsert rows from *df* into PostgreSQL prices table.
    Returns (rows_inserted, error_message).
    """
    if df.empty:
        return 0, "DataFrame is empty — nothing to push."

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(pg_url, pool_pre_ping=True)

        # Ensure table exists
        create_sql = text(
            """
            CREATE TABLE IF NOT EXISTS prices (
                symbol    VARCHAR(20)  NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                open      DOUBLE PRECISION,
                high      DOUBLE PRECISION,
                low       DOUBLE PRECISION,
                close     DOUBLE PRECISION,
                volume    BIGINT,
                PRIMARY KEY (symbol, timestamp)
            )
        """
        )
        with engine.begin() as conn:
            conn.execute(create_sql)

        # Upsert via temp table approach for speed
        tmp_df = df.copy()
        tmp_df.columns = [c.lower() for c in tmp_df.columns]

        with engine.begin() as conn:
            # Write to temp table
            tmp_df.to_sql("prices_tmp", conn, if_exists="replace", index=False)
            upsert_sql = text(
                """
                INSERT INTO prices (symbol, timestamp, open, high, low, close, volume)
                SELECT symbol, timestamp::timestamptz, open, high, low, close, volume
                FROM prices_tmp
                ON CONFLICT (symbol, timestamp) DO UPDATE SET
                    open   = EXCLUDED.open,
                    high   = EXCLUDED.high,
                    low    = EXCLUDED.low,
                    close  = EXCLUDED.close,
                    volume = EXCLUDED.volume
            """
            )
            conn.execute(upsert_sql)
            conn.execute(text("DROP TABLE IF EXISTS prices_tmp"))

        engine.dispose()
        return len(tmp_df), ""

    except Exception as e:
        return 0, str(e)


# ── Page ──────────────────────────────────────────────────────────────────────


def main() -> None:
    """Data Explorer page."""

    st.markdown(
        """
        <div style="
            background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);
            border:1px solid #334155;border-radius:14px;
            padding:22px 24px 16px;margin-bottom:20px
        ">
            <h2 style="margin:0;color:#e2e8f0">🔍 Data Explorer</h2>
            <p style="color:#94a3b8;margin:6px 0 0;font-size:0.92rem">
                Browse raw OHLCV data stored in DuckDB · export to CSV · push to PostgreSQL
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── DuckDB status banner ─────────────────────────────────────────────────
    stats = load_db_stats()
    if not stats:
        st.warning(
            "⚠️ No data found in DuckDB yet. "
            "Go to **Stock Overview**, load some symbols first, "
            "or run: `uv run python -m scripts.refresh_data --all`"
        )
        return

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("📦 Total Rows", f"{stats.get('total_rows', 0):,}")
    s2.metric("🏷️ Symbols", stats.get("symbols", 0))
    s3.metric("📅 Earliest", stats.get("earliest", "—"))
    s4.metric("📅 Latest", stats.get("latest", "—"))
    s5.metric("💾 DB Size", f"{stats.get('size_mb', 0)} MB")

    st.divider()

    # ── Filters ──────────────────────────────────────────────────────────────
    all_symbols = load_symbols()

    col_sym, col_start, col_end, col_rows = st.columns([3, 2, 2, 1])

    with col_sym:
        selected = st.multiselect(
            "Symbols",
            options=all_symbols,
            default=all_symbols[:3] if all_symbols else [],
            help="Select one or more symbols to view",
        )
    with col_start:
        start_dt = st.date_input("From date", value=date.today() - timedelta(days=90))
    with col_end:
        end_dt = st.date_input("To date", value=date.today())
    with col_rows:
        max_rows = st.number_input(
            "Max rows", value=500, min_value=10, max_value=10_000, step=100
        )

    if not selected:
        st.info("👆 Select at least one symbol to load data.")
        return

    # ── Load data ────────────────────────────────────────────────────────────
    with st.spinner("Loading from DuckDB…"):
        df = load_prices_from_duck(selected, start_dt, end_dt)

    if df.empty:
        st.warning(
            f"No rows found for **{', '.join(selected)}** "
            f"between {start_dt} and {end_dt}.\n\n"
            "Try widening the date range or loading data on **Stock Overview** first."
        )
        return

    # Trim to max_rows
    total_available = len(df)
    df = df.head(max_rows)

    # ── Tabs: table | stats | charts ─────────────────────────────────────────
    tab_data, tab_stats, tab_push = st.tabs(
        ["📋 Data Table", "📊 Summary Stats", "🚀 Push to PostgreSQL"]
    )

    # ── TAB 1: Data table ────────────────────────────────────────────────────
    with tab_data:
        st.markdown(
            f"Showing **{len(df):,}** of **{total_available:,}** rows "
            f"· {len(selected)} symbol(s) · {start_dt} → {end_dt}"
        )

        # Format display DF
        disp = df.copy()
        disp["timestamp"] = pd.to_datetime(disp["timestamp"]).dt.strftime("%Y-%m-%d")
        for col in ["open", "high", "low", "close"]:
            if col in disp.columns:
                disp[col] = disp[col].round(4)

        st.dataframe(disp, use_container_width=True, height=420)

        # CSV download
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            label="⬇️ Download as CSV",
            data=csv_buf.getvalue(),
            file_name=f"prices_{'_'.join(selected)}_{date.today()}.csv",
            mime="text/csv",
        )

    # ── TAB 2: Summary stats ─────────────────────────────────────────────────
    with tab_stats:
        for sym in selected:
            sym_df = df[df["symbol"] == sym]
            if sym_df.empty:
                continue
            st.markdown(f"#### {sym} — {len(sym_df):,} rows")
            num_cols = [
                c
                for c in ["open", "high", "low", "close", "volume"]
                if c in sym_df.columns
            ]
            st.dataframe(sym_df[num_cols].describe().round(4), use_container_width=True)

            # Latest close
            latest_row = sym_df.sort_values("timestamp").iloc[-1]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Latest Close", f"{latest_row.get('close', 0):.4f}")
            c2.metric("Latest High", f"{latest_row.get('high', 0):.4f}")
            c3.metric("Latest Low", f"{latest_row.get('low', 0):.4f}")
            c4.metric("Latest Vol", f"{int(latest_row.get('volume', 0)):,}")
            st.divider()

    # ── TAB 3: Push to PostgreSQL ─────────────────────────────────────────────
    with tab_push:
        st.markdown("""
            Push the data currently visible in the table above into **PostgreSQL**.
            The `prices` table will be created automatically if it doesn't exist.
            Rows are **upserted** (no duplicates).
            """)

        # Read PG URL from env or let user enter it
        pg_url_env = os.getenv("POSTGRES_URL", "")
        pg_url = st.text_input(
            "PostgreSQL connection URL",
            value=pg_url_env
            or "postgresql+psycopg2://postgres:postgres@localhost:5432/stocks",
            type="password",
            help="Format: postgresql+psycopg2://user:password@host:port/dbname",
        )

        push_symbols = st.multiselect(
            "Symbols to push",
            options=selected,
            default=selected,
            help="Choose which of the loaded symbols to send to PostgreSQL",
        )

        st.info(
            f"📤 Ready to push **{len(df[df['symbol'].isin(push_symbols)]):,} rows** "
            f"for symbols: **{', '.join(push_symbols)}**"
        )

        if st.button(
            "🚀 Push to PostgreSQL", type="primary", disabled=not push_symbols
        ):
            push_df = df[df["symbol"].isin(push_symbols)].copy()
            if push_df.empty:
                st.warning("Nothing to push — DataFrame is empty for selected symbols.")
            else:
                with st.spinner(f"Pushing {len(push_df):,} rows to PostgreSQL…"):
                    rows_inserted, err = push_to_postgres(push_df, pg_url)

                if err:
                    st.error(f"❌ Push failed: {err}")
                    st.markdown(
                        "**Tip:** Make sure PostgreSQL is running:\n"
                        "```bash\ndocker-compose up -d postgres\n```"
                    )
                else:
                    st.success(
                        f"✅ Successfully upserted **{rows_inserted:,} rows** into PostgreSQL `prices` table!"
                    )
                    st.balloons()

        st.divider()
        st.subheader("🕐 Automated Daily Sync")
        st.markdown("""
            To run this push automatically every day at a set time, use the built-in scheduler:

            ```bash
            # Run once immediately then every day at 08:00
            uv run python -m scripts.schedule_pg_sync --time 08:00 --symbols AAPL,MSFT,ITC.NS

            # Or refresh all symbols from symbols.toml
            uv run python -m scripts.schedule_pg_sync --time 08:00 --all
            ```

            The scheduler will:
            1. Download fresh data from **yfinance**
            2. Store in **DuckDB** (local cache)
            3. Upsert into **PostgreSQL** (persistent warehouse)

            > Set `POSTGRES_URL` in your `.env` file so the scheduler picks it up automatically.
            """)


if __name__ == "__main__":
    main()
