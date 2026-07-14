"""
Phase 1: Streamlit Multi-Page Application

Main entry point for the Streamlit app with authentication and page navigation.
"""

# Simple page router: import view modules lazily
from importlib import import_module

import streamlit as st

from app.config import AppConfig


def main():
    """Main Streamlit app entry point."""
    # TODO: Load config
    config = AppConfig()

    # TODO: Setup page configuration
    st.set_page_config(
        page_title=config.app_name,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    pages = [
        st.Page(
            import_module("app.views.page_01_home_dashboard").main,
            title="Home",
            icon="🏠",
            url_path="home",
        ),
        st.Page(
            import_module("app.views.page_02_stock_overview").main,
            title="Stock Overview",
            icon="📈",
            url_path="stock_overview",
        ),
        st.Page(
            import_module("app.views.page_03_data_explorer").main,
            title="Data Explorer",
            icon="🔍",
            url_path="data_explorer",
        ),
        st.Page(
            import_module("app.views.page_04_indicators").main,
            title="Indicators",
            icon="📊",
            url_path="indicators",
        ),
        st.Page(
            import_module("app.views.page_05_analysis").main,
            title="Analysis",
            icon="📉",
            url_path="analysis",
        ),
        st.Page(
            import_module("app.views.page_06_assistant_chat").main,
            title="Assistant Chat",
            icon="🤖",
            url_path="assistant_chat",
        ),
        st.Page(
            import_module("app.views.page_99_admin").main,
            title="Admin",
            icon="⚙️",
            url_path="admin",
        ),
    ]

    pg = st.navigation(pages)
    pg.run()


if __name__ == "__main__":
    main()
