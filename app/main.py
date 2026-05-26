"""
Phase 1: Streamlit Multi-Page Application

Main entry point for the Streamlit app with authentication and page navigation.

Displays project status and routes to appropriate views.

See docs/PROJECT_STATUS.md for implementation progress tracking.
"""

import streamlit as st
from app.config import AppConfig
from importlib import import_module
from pathlib import Path


def show_project_status():
    """Display project status banner in sidebar."""
    try:
        status_file = Path(__file__).parent.parent / "docs" / "PROJECT_STATUS.md"
        if status_file.exists():
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 📊 Project Status")
            st.sidebar.markdown("**Overall: ~16% Complete**")
            st.sidebar.markdown("""
            - 🔄 Phase 1: 30%
            - 🟡 Phase 2: 20%
            - 🟡 Phase 3: 25%
            - ⚫ Phase 4: 0%
            - ⚫ Phase 5: 5%
            """)
            st.sidebar.markdown("[📈 View Detailed Status](docs/PROJECT_STATUS.md)")
            st.sidebar.markdown("---")
    except Exception as e:
        pass


def main():
    """Main Streamlit app entry point."""
    config = AppConfig()
    
    st.set_page_config(
        page_title="de-bootcamp-summer2026",
        page_icon="📊",
        layout="wide",
    )
    
    # Show status in sidebar
    show_project_status()
    
    # Page routing
    pages = {
        "🏠 Home": "app.views.01_Home_Dashboard",
        "📈 Stock Overview": "app.views.02_Stock_Overview",
        "🔍 Data Explorer": "app.views.03_Data_Explorer",
        "📊 Indicators": "app.views.04_Indicators",
        "📉 Analysis": "app.views.05_Analysis",
        "🤖 Assistant Chat": "app.views.06_Assistant_Chat",
        "⚙️ Admin": "app.views.99_Admin",
    }
    
    choice = st.sidebar.selectbox("Navigation", list(pages.keys()))
    
    try:
        module = import_module(pages[choice])
        if hasattr(module, "main"):
            module.main()
        else:
            st.error(f"Page {choice} has no main() function defined.")
    except Exception as e:
        st.error(f"Error loading page: {e}")

    
if __name__ == "__main__":
    main()

