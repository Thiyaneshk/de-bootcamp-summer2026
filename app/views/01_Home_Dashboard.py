"""
Phase 1: Home Dashboard

Landing page for the application.

Displays:
- Welcome message
- Project status overview
- Quick navigation
- Getting started guide
"""

import streamlit as st
import os
import re
from pathlib import Path


def load_project_status():
    """Load project status from PROJECT_STATUS.md file."""
    try:
        status_file = Path(__file__).parent.parent.parent / "docs" / "PROJECT_STATUS.md"
        if status_file.exists():
            with open(status_file, "r") as f:
                content = f.read()
            
            # Extract phase information from the table
            phases = []
            lines = content.split("\n")
            
            for i, line in enumerate(lines):
                if "Phase 1:" in line and "Streamlit" in line:
                    phases.append({
                        "name": "Phase 1: Streamlit + yfinance",
                        "status": "🔄 IN_PROGRESS",
                        "completion": 30,
                        "desc": "Multi-page app, yfinance wrapper, DuckDB setup"
                    })
                elif "Phase 2:" in line and "Airflow" in line:
                    phases.append({
                        "name": "Phase 2: Airflow + PostgreSQL",
                        "status": "🟡 PARTIAL",
                        "completion": 20,
                        "desc": "DAG scaffolding, ETL tasks defined"
                    })
                elif "Phase 3:" in line and "dbt" in line:
                    phases.append({
                        "name": "Phase 3: dbt Transformations",
                        "status": "🟡 PARTIAL",
                        "completion": 25,
                        "desc": "Staging & mart models created"
                    })
                elif "Phase 4:" in line and "Analytics" in line:
                    phases.append({
                        "name": "Phase 4: Analytics Dashboards",
                        "status": "⚫ PLANNED",
                        "completion": 0,
                        "desc": "Awaiting Phase 3 completion"
                    })
                elif "Phase 5:" in line and "LLM" in line:
                    phases.append({
                        "name": "Phase 5: LLM + RAG",
                        "status": "⚫ PLANNED",
                        "completion": 5,
                        "desc": "Stub files only"
                    })
            
            return phases, content
        return None, None
    except Exception as e:
        st.error(f"Error loading project status: {e}")
        return None, None


def main():
    """Home dashboard page."""
    st.set_page_config(page_title="Home - de-bootcamp", layout="wide")
    
    st.title("📊 de-bootcamp-summer2026")
    st.subheader("Data Engineering Learning Project")
    
    # Load status
    phases, full_content = load_project_status()
    
    # Welcome section
    st.markdown("""
    ### Welcome! 🎉
    
    This is a **progressive learning project** that teaches modern data engineering concepts 
    through hands-on implementation. Learn one phase at a time, building toward a complete 
    data stack with real-time financial data.
    """)
    
    # Project Status Overview
    st.markdown("---")
    st.markdown("## 📈 Project Implementation Status")
    st.markdown("**Overall Progress: ~16% Complete** | Last Updated: 2026-05-26")
    
    if phases:
        # Progress bar for overall project
        overall_completion = sum(p["completion"] for p in phases) / len(phases)
        st.progress(overall_completion / 100, text=f"{overall_completion:.0f}% Overall")
        
        # Individual phase cards
        cols = st.columns(1)
        for phase in phases:
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 1, 3, 1])
                
                with col1:
                    st.metric("Status", phase["status"])
                
                with col2:
                    st.metric("Progress", f"{phase['completion']}%")
                
                with col3:
                    st.write(f"**{phase['name']}**")
                    st.caption(phase['desc'])
                
                with col4:
                    st.progress(phase['completion'] / 100)
    
    # Quick Navigation
    st.markdown("---")
    st.markdown("## 🗺️ Navigation")
    
    nav_cols = st.columns(3)
    with nav_cols[0]:
        st.markdown("""
        ### 📱 Phase 1
        **Streamlit + yfinance**
        - Real-time stock data
        - DuckDB storage
        - Interactive dashboards
        """)
    
    with nav_cols[1]:
        st.markdown("""
        ### 🔄 Phase 2-3
        **Airflow + PostgreSQL + dbt**
        - Automated ETL pipelines
        - Data warehouse
        - Data transformations
        """)
    
    with nav_cols[2]:
        st.markdown("""
        ### 🤖 Phase 4-5
        **Analytics + LLM**
        - Advanced dashboards
        - AI-powered analysis
        - Natural language queries
        """)
    
    # Getting Started
    st.markdown("---")
    st.markdown("## 🚀 Getting Started")
    
    start_cols = st.columns(2)
    with start_cols[0]:
        st.markdown("""
        ### For Phase 1 (Streamlit)
        ```bash
        # Install dependencies
        uv sync --extra phase1
        
        # Run the app
        uv run streamlit run app/main.py
        ```
        Then explore:
        - **Stock Overview** → View real-time price data
        - **Data Explorer** → Analyze raw data
        """)
    
    with start_cols[1]:
        st.markdown("""
        ### For Phase 2+ (Full Stack)
        ```bash
        # Start all services
        docker-compose up
        
        # In another terminal
        uv run streamlit run app/main.py
        ```
        See [SETUP_COMMANDS.md](../SETUP_COMMANDS.md) for details
        """)
    
    # Key Stats
    st.markdown("---")
    st.markdown("## 📊 Project Stats")
    
    stat_cols = st.columns(4)
    with stat_cols[0]:
        st.metric("Total Phases", "5")
    with stat_cols[1]:
        st.metric("Phases Started", "3")
    with stat_cols[2]:
        st.metric("Files Created", "35+")
    with stat_cols[3]:
        st.metric("Estimated Hours", "8-15")
    
    # Important Links
    st.markdown("---")
    st.markdown("## 📚 Documentation")
    
    doc_cols = st.columns(3)
    with doc_cols[0]:
        st.markdown("""
        - 📊 [PROJECT_STATUS.md](../docs/PROJECT_STATUS.md) ⭐ **START HERE**
        - 📖 [README.md](../README.md)
        - ⚙️ [SETUP_COMMANDS.md](../SETUP_COMMANDS.md)
        """)
    
    with doc_cols[1]:
        st.markdown("""
        - 📱 [Phase 1: Streamlit](../docs/PHASE_1_STREAMLIT.md)
        - 🔄 [Phase 2: Airflow+Postgres](../docs/PHASE_2_AIRFLOW_POSTGRES.md)
        - 🔀 [Phase 3: dbt](../docs/PHASE_3_DBT.md)
        """)
    
    with doc_cols[2]:
        st.markdown("""
        - 📈 [Phase 4: Analytics](../docs/PHASE_4_ANALYTICS.md)
        - 🤖 [Phase 5: LLM+RAG](../docs/PHASE_5_LLM_RAG.md)
        """)
    
    # Footer with resources
    st.markdown("---")
    st.markdown("""
    ### 📖 Learning Resources
    - [yfinance Docs](https://github.com/ranaroussi/yfinance)
    - [Streamlit Docs](https://docs.streamlit.io/)
    - [Apache Airflow Guide](https://airflow.apache.org/)
    - [dbt Docs](https://docs.getdbt.com/)
    - [PostgreSQL Tutorials](https://www.postgresql.org/docs/15/)
    - [Ollama Models](https://ollama.ai/)
    
    **Next Steps:**
    1. Review [PROJECT_STATUS.md](../docs/PROJECT_STATUS.md) for detailed progress
    2. Navigate to the appropriate phase using the sidebar
    3. Follow the phase-specific guides for implementation
    """)


if __name__ == "__main__":
    main()

