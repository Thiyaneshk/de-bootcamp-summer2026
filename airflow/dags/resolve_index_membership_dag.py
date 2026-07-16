"""
Phase 10: Resolve Index Membership DAG

Weekly DAG that scrapes index constituent lists (S&P 500, NASDAQ-100, Nifty 50)
and upserts them into the registry tables.

Schedule: Every Sunday at 00:00 UTC
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Index scrapers
# ─────────────────────────────────────────────────────────────────────────────


def _scrape_sp500() -> list[dict]:
    """Scrape S&P 500 constituents from Wikipedia."""
    import pandas as pd

    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]  # First table is the current member list
    constituents = []
    for _, row in df.iterrows():
        sym = str(row.get("Symbol", "")).strip().replace(".", "-")
        name = str(row.get("Security", ""))
        sector = str(row.get("GICS Sector", ""))
        if sym:
            constituents.append({
                "stock_symbol": sym,
                "name": name,
                "sector": sector,
                "weight": None,
            })
    logger.info("Scraped %d S&P 500 constituents", len(constituents))
    return constituents


def _scrape_nasdaq100() -> list[dict]:
    """Scrape NASDAQ-100 constituents from Wikipedia."""
    import pandas as pd

    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    tables = pd.read_html(url)
    # The constituents table typically has 'Ticker' and 'Company' columns
    df = None
    for tbl in tables:
        cols_lower = [c.lower() for c in tbl.columns]
        if "ticker" in cols_lower or "symbol" in cols_lower:
            df = tbl
            break
    if df is None and len(tables) > 3:
        df = tables[3]  # Fallback: usually the 4th table

    constituents = []
    if df is not None:
        for _, row in df.iterrows():
            sym = None
            for col in ["Ticker", "Symbol", "ticker", "symbol"]:
                if col in row.index:
                    sym = str(row[col]).strip()
                    break
            name = ""
            for col in ["Company", "Security", "company", "security"]:
                if col in row.index:
                    name = str(row[col]).strip()
                    break
            if sym and sym != "nan":
                constituents.append({
                    "stock_symbol": sym.replace(".", "-"),
                    "name": name,
                    "weight": None,
                })
    logger.info("Scraped %d NASDAQ-100 constituents", len(constituents))
    return constituents


def _scrape_nifty50() -> list[dict]:
    """Scrape Nifty 50 constituents from Wikipedia."""
    import pandas as pd

    url = "https://en.wikipedia.org/wiki/NIFTY_50"
    tables = pd.read_html(url)
    df = None
    for tbl in tables:
        cols_lower = [c.lower() for c in tbl.columns]
        if "symbol" in cols_lower or "company" in cols_lower:
            df = tbl
            break
    if df is None and len(tables) > 1:
        df = tables[1]

    constituents = []
    if df is not None:
        for _, row in df.iterrows():
            sym = None
            for col in ["Symbol", "symbol", "NSE Symbol"]:
                if col in row.index:
                    sym = str(row[col]).strip()
                    break
            name = ""
            for col in ["Company name", "Company", "company"]:
                if col in row.index:
                    name = str(row[col]).strip()
                    break
            if sym and sym != "nan":
                # Append .NS suffix for NSE symbols
                yf_sym = f"{sym}.NS" if not sym.endswith(".NS") else sym
                constituents.append({
                    "stock_symbol": yf_sym,
                    "name": name,
                    "weight": None,
                })
    logger.info("Scraped %d Nifty 50 constituents", len(constituents))
    return constituents


# ─────────────────────────────────────────────────────────────────────────────
# Main task
# ─────────────────────────────────────────────────────────────────────────────

INDEX_SCRAPERS = {
    "^GSPC": ("S&P 500", _scrape_sp500),
    "^NDX": ("NASDAQ-100", _scrape_nasdaq100),
    "^NSEI": ("Nifty 50", _scrape_nifty50),
}


def resolve_all_indices(**context) -> dict:
    """Scrape all configured indices and upsert into the registry."""
    from app.db.registry import add_instrument, upsert_index_constituents

    summary = {}

    for index_symbol, (index_name, scraper_fn) in INDEX_SCRAPERS.items():
        try:
            # Register the index itself
            add_instrument(
                index_symbol,
                name=index_name,
                instrument_type="index",
                exchange="INDEX",
                is_active=True,
            )

            # Scrape constituents
            constituents = scraper_fn()

            # Register each constituent as an active stock
            for c in constituents:
                add_instrument(
                    c["stock_symbol"],
                    name=c.get("name", ""),
                    instrument_type="stock",
                    exchange="US" if not c["stock_symbol"].endswith(".NS") else "NSE",
                    is_active=True,
                )

            # Store membership mapping
            upsert_index_constituents(index_symbol, constituents)

            summary[index_symbol] = {
                "name": index_name,
                "constituents_count": len(constituents),
                "status": "success",
            }
            logger.info("✅ %s: %d constituents", index_name, len(constituents))

        except Exception as e:
            logger.error("❌ Failed to resolve %s: %s", index_symbol, e)
            summary[index_symbol] = {"name": index_name, "status": "failed", "error": str(e)}

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# DAG definition
# ─────────────────────────────────────────────────────────────────────────────

default_args = {
    "owner": "data-eng",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "start_date": datetime(2026, 5, 1),
    "email_on_failure": False,
    "depends_on_past": False,
}

with DAG(
    dag_id="resolve_index_membership",
    default_args=default_args,
    description="Weekly: Scrape S&P 500, NASDAQ-100, Nifty 50 → registry",
    schedule="0 0 * * 0",  # Every Sunday at midnight UTC
    catchup=False,
    max_active_runs=1,
    tags=["registry", "index", "membership", "scraping"],
) as dag:

    PythonOperator(
        task_id="resolve_all_indices",
        python_callable=resolve_all_indices,
        doc_md="Scrape S&P 500, NASDAQ-100, Nifty 50 from Wikipedia and upsert into registry",
    )
