# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- **Phase 10: Ticker Registry**
  - Built robust database-backed ticker registry in PostgreSQL/DuckDB.
  - Implemented Streamlit UI (`page_07_ticker_registry.py`) for managing tracked symbols, seeding data, and checking ingestion logs.
  - Added CSV seed functionality (`data/ticker_registry_seed.csv`) for ~193 active instruments across IN, CA, and US markets.
  - Rewrote Airflow ETL DAG to use **Dynamic Task Mapping** (`expand()`), running daily ingestions in parallel per active symbol.
  - Implemented weekly DAG (`resolve_index_membership_dag.py`) to automatically scrape S&P 500, NASDAQ-100, and Nifty 50 constituents from Wikipedia.
  - Added resilient DuckDB fallback across the app when PostgreSQL is unreachable.
- **Phase 9: Terraform Infrastructure**
  - Infrastructure as code setup for provisioning cloud resources.
- **Phase 8: Databricks Integration**
  - Scaffold for PySpark ETL and Delta Lake integrations (planned for machine learning tasks).

### Changed
- UI Overhaul: Unified gradient banners, full-width layouts, and responsive elements across all Streamlit pages.
- Standardized automated testing via `run_tests.py` using `pytest`.

## [Initial Phases (1-7)]
- **Phase 7:** Snowflake Cloud Data Warehouse integration and dbt target.
- **Phase 6:** Redis distributed caching for Streamlit and ETL functions.
- **Phase 5:** LLM Integration + RAG-based analysis using local Ollama.
- **Phase 4:** Analytics dashboards and insight visualizations using Plotly.
- **Phase 3:** dbt data transformations, staging models, and marts.
- **Phase 2:** Apache Airflow orchestration and PostgreSQL DW setup via Docker.
- **Phase 1:** Streamlit multi-page UI, yfinance API ingestion, and local DuckDB storage.
