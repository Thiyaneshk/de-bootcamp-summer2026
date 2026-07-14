"""Ticker registry management page."""

from __future__ import annotations

import streamlit as st

from app.db.registry import (
    add_instrument,
    get_active_symbols,
    get_instruments,
    log_ingestion,
    set_instrument_active,
    upsert_index_constituents,
)


def main() -> None:
    st.set_page_config(page_title="Ticker Registry", layout="wide")
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);padding:20px;border-radius:14px;margin-bottom:18px">
            <h2 style="margin:0;color:#f8fafc">📋 Ticker Registry</h2>
            <p style="margin:6px 0 0;color:#cbd5e1">Manage instruments, index memberships, and ingestion history.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.subheader("Add instrument")
        symbol = st.text_input("Symbol", placeholder="AAPL")
        name = st.text_input("Name", placeholder="Apple Inc.")
        instrument_type = st.selectbox("Type", ["stock", "etf", "index", "crypto"])
        exchange = st.text_input("Exchange", placeholder="NASDAQ")
        is_active = st.checkbox("Active", value=True)
        if st.button("Save instrument", type="primary"):
            if symbol:
                add_instrument(symbol, name=name, instrument_type=instrument_type, exchange=exchange, is_active=is_active)
                st.success(f"Saved {symbol}")

    tab_registry, tab_membership, tab_history = st.tabs(["Registry", "Membership", "Ingestion History"])

    with tab_registry:
        st.subheader("Known instruments")
        instrument_type_filter = st.selectbox("Filter by type", ["all", "stock", "etf", "index", "crypto"], index=0)
        instruments = get_instruments(
            instrument_type=None if instrument_type_filter == "all" else instrument_type_filter
        )
        if instruments:
            for item in instruments:
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                col1.write(item["symbol"])
                col2.write(item.get("name") or "")
                col3.write(item.get("instrument_type", ""))
                if col4.button(f"Toggle {item['symbol']}", key=f"toggle_{item['symbol']}"):
                    set_instrument_active(item["symbol"], not item.get("is_active", True))
                    st.rerun()
        else:
            st.info("No instruments registered yet.")

    with tab_membership:
        st.subheader("Index constituents")
        if st.button("Seed sample S&P 500 membership"):
            upsert_index_constituents("^GSPC", [{"stock_symbol": "AAPL", "weight": 0.06}, {"stock_symbol": "MSFT", "weight": 0.05}])
            st.success("Sample membership saved")
        st.write("Active symbols: ")
        st.code(get_active_symbols())

    with tab_history:
        st.subheader("Recent ingestion log")
        log_ingestion("AAPL", "daily", "success", rows_ingested=12)
        logs = log_ingestion("AAPL", "daily", "success", rows_ingested=12)
        st.dataframe(logs, use_container_width=True)
