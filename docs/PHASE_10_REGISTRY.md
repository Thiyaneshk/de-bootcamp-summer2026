# Phase 10: Ticker Registry & Airflow Redesign

## Goal
Replace the flat `symbols.toml` file with a database-backed registry of indices, ETFs, and individual stocks. Redesign the Airflow ingestion DAG to process these symbols dynamically.

## Key Concepts Covered
- Database-backed configuration mapping
- Airflow dynamic task mapping using `expand()`
- Auditable ingestion logs

## Core Tasks
1. **Database Schema Setup**
   - Tables: `registry.instruments`, `registry.index_constituents`, and `registry.ingestion_log`.
2. **Streamlit UI**
   - Added **"📋 Ticker Registry"** page to browse, add, and toggle active instruments, as well as view ingestion histories.
3. **Airflow DAG Redesign**
   - Switched from monolithic monolithic functions sequentially downloading all symbols to a scalable per-symbol approach.
   - `get_active_symbols` gets a list of active tickers from `registry.instruments`.
   - `download_one_by_one` runs dynamically via `.expand()` to ingest symbols in parallel to DuckDB and push individually to PostgreSQL, followed by a log event to `registry.ingestion_log`.

## Important Note on Indexes
Instead of automating wikipedia scraping (which is prone to failures, blocks, and schema changes), index membership (e.g. S&P 500 constituents) can be seeded via the UI's Ticker Registry tab manually as part of routine maintenance.
