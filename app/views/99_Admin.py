"""
Phase 1+ / Phase 2+: Admin Panel

Administrative controls for monitoring database schemas, cleaning cached states,
manually triggering ETL ingestion, and inspecting environment configuration.
"""

import os
import logging
import subprocess
from pathlib import Path
import streamlit as st
import duckdb
import toml
from sqlalchemy import create_engine, text
import ollama

from scripts.refresh_data import refresh_symbols, refresh_all
from app.config import AppConfig

logger = logging.getLogger(__name__)


def check_duckdb_status(db_path: str) -> dict:
    """Check DuckDB file presence and rows count."""
    status = {"exists": False, "size_mb": 0.0, "row_count": 0, "error": None}
    try:
        path = Path(db_path)
        if path.exists():
            status["exists"] = True
            status["size_mb"] = round(path.stat().st_size / (1024 * 1024), 2)
            
            conn = duckdb.connect(db_path)
            # check if prices table exists
            t_check = conn.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_name = 'prices'"
            ).fetchone()[0]
            if t_check > 0:
                rows = conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
                status["row_count"] = rows
            conn.close()
    except Exception as e:
        status["error"] = str(e)
    return status


def check_postgres_status(pg_url: str) -> dict:
    """Check PostgreSQL connection, active schemas, and table row counts."""
    status = {
        "connected": False,
        "error": None,
        "schemas": [],
        "tables": {}
    }
    if not pg_url:
        status["error"] = "POSTGRES_URL environment variable is not set."
        return status

    try:
        engine = create_engine(pg_url, pool_pre_ping=True)
        with engine.connect() as conn:
            status["connected"] = True
            
            # Schemas check
            schemas_res = conn.execute(text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name IN ('public', 'public_staging', 'public_marts')"
            )).fetchall()
            status["schemas"] = [r[0] for r in schemas_res]
            
            # Row counts in tables
            tables_to_check = [
                ("public", "prices"),
                ("public_staging", "stg_prices"),
                ("public_marts", "fct_daily_prices"),
                ("public_marts", "fct_technical_indicators")
            ]
            
            for schema, table in tables_to_check:
                try:
                    count_res = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{table}")).scalar()
                    status["tables"][f"{schema}.{table}"] = f"{count_res:,} rows"
                except Exception:
                    status["tables"][f"{schema}.{table}"] = "❌ Table missing/unpopulated"
        engine.dispose()
    except Exception as e:
        status["error"] = str(e)
    return status


def check_ollama_status() -> dict:
    """Check Ollama service connection and installed models."""
    status = {"running": False, "models": [], "error": None}
    try:
        models_data = ollama.list()
        status["running"] = True
        status["models"] = [m.model for m in models_data.models]
    except Exception as e:
        status["error"] = str(e)
    return status


def run_dbt_command() -> tuple[bool, str]:
    """Execute dbt run command locally."""
    try:
        project_root = Path(__file__).parent.parent.parent
        dbt_dir = project_root / "dbt"
        
        # Run dbt run against prod target
        cmd = ["uv", "run", "dbt", "run", "--profiles-dir", str(dbt_dir), "--target", "prod"]
        res = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True, timeout=90)
        
        if res.returncode == 0:
            return True, res.stdout
        else:
            return False, res.stderr + "\n" + res.stdout
    except Exception as e:
        return False, str(e)


def main():
    """Admin panel entry point."""
    
    st.markdown(
        """
        <div style="
            background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);
            border:1px solid #475569;border-radius:14px;
            padding:22px 24px 16px;margin-bottom:20px
        ">
            <h2 style="margin:0;color:#f1f5f9">⚙️ Admin Panel</h2>
            <p style="color:#cbd5e1;margin:6px 0 0;font-size:0.92rem">
                Monitor database health · Clear application memory · Trigger manual sync and dbt transformations
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    config = AppConfig()

    tab_status, tab_refresh, tab_config = st.tabs([
        "🛡️ System Status", 
        "🔄 Manual Refreshes", 
        "📝 Configurations"
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: System Status & Cache Clear
    # ─────────────────────────────────────────────────────────────────────────
    with tab_status:
        st.subheader("Database & AI Integrations Status")
        
        # 1. DuckDB status
        duck_status = check_duckdb_status(config.duckdb_path)
        with st.expander("📦 DuckDB Cache Status", expanded=True):
            if duck_status["exists"]:
                st.success(f"DuckDB database exists at `{config.duckdb_path}`")
                c1, c2 = st.columns(2)
                c1.metric("File Size", f"{duck_status['size_mb']} MB")
                c2.metric("Raw Prices Count", f"{duck_status['row_count']:,} rows")
            else:
                st.warning(f"DuckDB database file not found at `{config.duckdb_path}`")
                if duck_status["error"]:
                    st.error(f"Error checking DuckDB: {duck_status['error']}")

        # 2. PostgreSQL status
        pg_status = check_postgres_status(config.postgres_url)
        with st.expander("🐘 PostgreSQL Warehouse Status", expanded=True):
            if pg_status["connected"]:
                st.success("PostgreSQL database connection successful!")
                
                # Active schemas check
                st.markdown(f"**Discovered Schemas:** {', '.join([f'`{s}`' for s in pg_status['schemas']])}")
                
                # Tables row counts
                st.markdown("**Table Stats:**")
                for table, stat in pg_status["tables"].items():
                    st.markdown(f" - `{table}`: **{stat}**")
            else:
                st.error("Could not connect to PostgreSQL database.")
                st.markdown(f"**Connection Error:** `{pg_status['error']}`")
                st.info("Check if Postgres container is running: `docker-compose up -d postgres`")

        # 3. Ollama status
        oll_status = check_ollama_status()
        with st.expander("🤖 Ollama LLM Connection", expanded=True):
            if oll_status["running"]:
                st.success("Ollama service reached successfully!")
                st.markdown(f"**Available local models:** {', '.join([f'`{m}`' for m in oll_status['models']])}")
            else:
                st.error("Ollama service could not be reached at http://localhost:11434")
                st.markdown(f"**Connection Error:** `{oll_status['error']}`")
                st.info("Ensure Ollama application is running on your Mac.")

        # Cache Clear Section
        st.divider()
        st.subheader("Cache Management")
        st.markdown(
            "Streamlit caches database rows to accelerate dashboards. "
            "If you refresh data or adjust dbt models, clear the cache to reload fresh metrics."
        )
        if st.button("🧹 Clear Streamlit Application Cache", type="primary"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Success: All application caches cleared!")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: Manual Ingest and dbt run
    # ─────────────────────────────────────────────────────────────────────────
    with tab_refresh:
        st.subheader("Manual Data Ingestion")
        st.markdown(
            "Trigger Yahoo Finance fetches manually. "
            "Fresh rows will be added to PostgreSQL or DuckDB based on your active configurations."
        )

        symbols_to_refresh = st.multiselect(
            "Select Tickers to Ingest",
            options=config.symbols,
            default=config.symbols[:3] if config.symbols else []
        )

        col_ref_sel, col_ref_all = st.columns(2)
        
        with col_ref_sel:
            if st.button("🚀 Refresh Selected Tickers", type="primary", disabled=not symbols_to_refresh):
                with st.spinner(f"Pulling data for {', '.join(symbols_to_refresh)}..."):
                    refresh_symbols(symbols_to_refresh)
                st.success("ETL price ingestion finished!")
                st.cache_data.clear()
                
        with col_ref_all:
            if st.button("🔄 Ingest All Configured Symbols", type="secondary"):
                with st.spinner("Syncing all symbols from symbols.toml..."):
                    refresh_all()
                st.success("ETL bulk sync finished!")
                st.cache_data.clear()

        st.divider()
        st.subheader("dbt Transformations Pipeline")
        st.markdown(
            "Execute the dbt compilation & transformation pipeline locally. "
            "This will rebuild the staging views and marts schemas (`stg_prices`, `fct_daily_prices`, `fct_technical_indicators`)."
        )
        
        if st.button("🔧 Trigger dbt transformation run", type="primary"):
            with st.spinner("Compiling and executing dbt models..."):
                success, output = run_dbt_command()
                
            if success:
                st.success("✅ dbt transformations completed successfully!")
                with st.expander("Output Logs"):
                    st.text(output)
                st.cache_data.clear()
            else:
                st.error("❌ dbt run encountered errors.")
                with st.expander("Error Logs"):
                    st.text(output)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3: Config viewer
    # ─────────────────────────────────────────────────────────────────────────
    with tab_config:
        st.subheader("Environment Settings")
        
        # Env variables
        masked_pg = "Not Set"
        if config.postgres_url:
            # Mask username/password for security
            masked_pg = config.postgres_url
            if "@" in masked_pg:
                parts = masked_pg.split("@")
                sub_parts = parts[0].split(":")
                if len(sub_parts) > 2:
                    masked_pg = f"{sub_parts[0]}:***@{parts[1]}"
                    
        st.markdown("**Configurations Loaded:**")
        st.markdown(f" - **`APP_ENV`**: `{config.app_env}`")
        st.markdown(f" - **`DUCKDB_PATH`**: `{config.duckdb_path}`")
        st.markdown(f" - **`POSTGRES_URL`**: `{masked_pg}`")
        
        st.divider()
        st.subheader("Symbols TOML File")
        
        try:
            project_root = Path(__file__).parent.parent.parent
            toml_path = project_root / "config" / "symbols.toml"
            if toml_path.exists():
                with open(toml_path, "r") as f:
                    toml_content = f.read()
                st.code(toml_content, language="toml")
            else:
                st.warning("`config/symbols.toml` file not found.")
        except Exception as e:
            st.error(f"Could not read symbols TOML: {e}")


if __name__ == "__main__":
    main()
