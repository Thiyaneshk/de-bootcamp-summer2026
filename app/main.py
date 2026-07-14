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
    # Load config
    if "config" not in st.session_state:
        st.session_state.config = AppConfig()

    # Setup page configuration
    st.set_page_config(
        page_title=st.session_state.config.app_name,
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("de-bootcamp-summer2026")
    st.write("Data Engineering Learning Project")

    pages = {
        "Home": "app.views.page_01_home_dashboard",
        "Stock Overview": "app.views.page_02_stock_overview",
        "Data Explorer": "app.views.page_03_data_explorer",
        "Indicators": "app.views.page_04_indicators",
        "Analysis": "app.views.page_05_analysis",
        "Assistant Chat": "app.views.page_06_assistant_chat",
        "Admin": "app.views.page_99_admin",
    }

    choice = st.sidebar.selectbox("Page", list(pages.keys()))
    module = import_module(pages[choice])
    # Each view exposes a `main()` function
    if hasattr(module, "main"):
        module.main()
    else:
        st.write(f"Page {choice} has no main() to run.")


if __name__ == "__main__":
    main()
