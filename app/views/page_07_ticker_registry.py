"""
Phase 10: Ticker Registry — Manage instruments, index memberships, and ingestion history.

Browse, add, and toggle active/inactive instruments. Seed from CSV.
View index constituents and recent ingestion logs.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.db.registry import (
    add_instrument,
    get_active_symbols,
    get_instruments,
    init_registry_tables,
    set_instrument_active,
)


def main() -> None:
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);
                    padding:24px 28px;border-radius:14px;margin-bottom:18px">
            <h2 style="margin:0;color:#f8fafc">📋 Ticker Registry</h2>
            <p style="margin:6px 0 0;color:#cbd5e1">
                Manage instruments · Index memberships · Ingestion history
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Ensure tables exist
    try:
        init_registry_tables()
    except Exception:
        pass

    # ── Sidebar — Add Instrument ──────────────────────────────────────────────
    with st.sidebar:
        st.subheader("➕ Add Instrument")
        with st.form("add_instrument_form", clear_on_submit=True):
            sym = st.text_input("Symbol", placeholder="AAPL").strip().upper()
            name = st.text_input("Name", placeholder="Apple Inc.")
            itype = st.selectbox("Type", ["stock", "etf", "index", "crypto"])
            exchange = st.text_input("Exchange", placeholder="NASDAQ")
            is_active = st.checkbox("Active", value=True)
            submitted = st.form_submit_button(
                "💾 Save", type="primary", use_container_width=True
            )
            if submitted and sym:
                add_instrument(
                    sym,
                    name=name,
                    instrument_type=itype,
                    exchange=exchange,
                    is_active=is_active,
                )
                st.success(f"✅ Saved **{sym}**")
                st.rerun()

        st.divider()
        st.subheader("📥 Seed from CSV")
        if st.button(
            "🌱 Load seed data",
            use_container_width=True,
            help="Loads ~193 instruments from data/ticker_registry_seed.csv",
        ):
            try:
                from scripts.seed_registry import seed

                result = seed()
                st.success(f"Seeded {result['inserted']}/{result['total']} instruments")
                st.rerun()
            except Exception as e:
                st.error(f"Seed failed: {e}")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_registry, tab_membership, tab_history = st.tabs(
        ["📊 Instrument Registry", "🔗 Index Membership", "📜 Ingestion History"]
    )

    # ── Tab 1: Instrument Registry ────────────────────────────────────────────
    with tab_registry:
        col_filter, col_stats = st.columns([2, 3])
        with col_filter:
            type_filter = st.selectbox(
                "Filter by type",
                ["all", "stock", "etf", "index", "crypto"],
                index=0,
                label_visibility="collapsed",
            )

        instruments = get_instruments(
            instrument_type=None if type_filter == "all" else type_filter
        )
        active_count = sum(1 for i in instruments if i.get("is_active"))

        with col_stats:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total", len(instruments))
            c2.metric("Active", active_count)
            c3.metric("Inactive", len(instruments) - active_count)

        if instruments:
            # Convert to DataFrame for display
            df = pd.DataFrame(instruments)
            df["is_active"] = df["is_active"].apply(lambda x: "✅" if x else "❌")
            df.columns = ["Symbol", "Name", "Type", "Exchange", "Active"]

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                height=min(400, 35 * len(df) + 38),
            )

            # Toggle controls
            st.markdown("---")
            toggle_col1, toggle_col2, toggle_col3 = st.columns([2, 1, 1])
            with toggle_col1:
                sym_to_toggle = st.selectbox(
                    "Select symbol to toggle",
                    [
                        i["symbol"]
                        for i in get_instruments(
                            instrument_type=None
                            if type_filter == "all"
                            else type_filter
                        )
                    ],
                    label_visibility="collapsed",
                )
            with toggle_col2:
                if st.button("🔄 Toggle Active", use_container_width=True):
                    current = next(
                        (i for i in get_instruments() if i["symbol"] == sym_to_toggle),
                        None,
                    )
                    if current:
                        set_instrument_active(sym_to_toggle, not current["is_active"])
                        st.rerun()
            with toggle_col3:
                if st.button("✅ Enable All", use_container_width=True):
                    for i in instruments:
                        set_instrument_active(i["symbol"], True)
                    st.rerun()
        else:
            st.info(
                "No instruments registered yet. Use the sidebar to add one or seed from CSV."
            )

    # ── Tab 2: Index Membership ───────────────────────────────────────────────
    with tab_membership:
        st.markdown("#### Index Constituents")
        st.caption(
            "View which stocks belong to each index. "
            "The weekly Airflow DAG `resolve_index_membership` auto-discovers these."
        )

        active_syms = get_active_symbols()
        if active_syms:
            st.success(f"**{len(active_syms)}** active symbols ready for ingestion")
            with st.expander("View active symbols", expanded=False):
                st.code(", ".join(active_syms))
        else:
            st.warning("No active symbols. Seed the registry first.")

    # ── Tab 3: Ingestion History ──────────────────────────────────────────────
    with tab_history:
        st.markdown("#### Recent Ingestion Log")
        st.caption("Shows the last 10 ingestion results logged by the ETL pipeline.")

        # Read-only: query existing logs without writing
        try:
            from sqlalchemy import text as sa_text

            from app.db.connection import get_duckdb_connection
            from app.db.registry import _get_postgres_engine

            engine = _get_postgres_engine()
            if engine:
                with engine.connect() as conn:
                    rows = conn.execute(
                        sa_text(
                            "SELECT symbol, ingestion_type, status, rows_ingested, "
                            "started_at, completed_at FROM ingestion_log "
                            "ORDER BY id DESC LIMIT 20"
                        )
                    ).fetchall()
                engine.dispose()
                if rows:
                    log_df = pd.DataFrame(
                        rows,
                        columns=[
                            "Symbol",
                            "Type",
                            "Status",
                            "Rows",
                            "Started",
                            "Completed",
                        ],
                    )
                    st.dataframe(log_df, use_container_width=True, hide_index=True)
                else:
                    st.info(
                        "No ingestion logs yet. Run the Airflow ETL DAG to populate this."
                    )
            else:
                with get_duckdb_connection() as conn:
                    try:
                        rows = conn.execute(
                            "SELECT symbol, ingestion_type, status, rows_ingested, "
                            "started_at, completed_at FROM ingestion_log "
                            "ORDER BY id DESC LIMIT 20"
                        ).fetchall()
                        if rows:
                            log_df = pd.DataFrame(
                                rows,
                                columns=[
                                    "Symbol",
                                    "Type",
                                    "Status",
                                    "Rows",
                                    "Started",
                                    "Completed",
                                ],
                            )
                            st.dataframe(
                                log_df, use_container_width=True, hide_index=True
                            )
                        else:
                            st.info(
                                "No ingestion logs yet. Run the Airflow ETL DAG to populate this."
                            )
                    except Exception:
                        st.info(
                            "Ingestion log table not initialized yet. Run the seed or ETL DAG first."
                        )
        except Exception as e:
            st.warning(f"Could not read ingestion log: {e}")
