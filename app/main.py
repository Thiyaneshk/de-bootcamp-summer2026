"""
Phase 1: Streamlit Multi-Page Application

Main entry point for the Streamlit app with authentication and page navigation.
TODO: Implement multi-page structure with streamlit.Page
"""

import streamlit as st
from app.config import AppConfig


def main():
    """Main Streamlit app entry point."""
    # TODO: Load config
    config = AppConfig()
    
    # TODO: Setup page configuration
    st.set_page_config(
        page_title="de-bootcamp-summer2026",
        page_icon="📊",
        layout="wide",
    )
    
    # TODO: Implement page routing
    # Pages to implement:
    # 1. Home Dashboard (landing page)
    # 2. Stock Overview (real-time data viewer)
    # 3. Data Explorer (raw data tables)
    # 4. Indicators (dbt-generated indicators, Phase 3+)
    # 5. Analysis (analytics dashboards, Phase 4+)
    # 6. AI Analyst (LLM/RAG chat, Phase 5+)
    # 99. Admin (admin controls & setup)
    
    st.title("de-bootcamp-summer2026")
    st.write("Data Engineering Learning Project")
    

if __name__ == "__main__":
    main()
