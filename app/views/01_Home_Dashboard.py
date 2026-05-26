"""
Phase 1: Home Dashboard

Landing page for the application.

TODO: Implement:
- Welcome message
- Navigation guide
- Quick stats (symbols count, last update, data points)
- Getting started instructions
"""

import pandas as pd
import streamlit as st


def main():
    """Home dashboard page."""
    st.title("📊 de-bootcamp-summer2026")
    st.subheader("Data Engineering Learning Project")
    
    # Welcome content
    st.write("Welcome to the learning project!")
    
    # Project Status Section
    st.markdown("---")
    st.header("📈 Project Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Phase", "1/5", "Streamlit")
    
    with col2:
        st.metric("Completion", "20%", "+5%")
    
    with col3:
        st.metric("Data Sources", "0", "Pending")
    
    with col4:
        st.metric("Components", "6", "Scaffolded")
    
    # Current Phase Details
    st.subheader("🎯 Current Phase: Streamlit Frontend")
    st.write("""
    - **Status**: Foundation & Setup
    - **Pages Scaffolded**: 6 multi-page app structure
    - **Features**: Authentication, Chat Interface, Analysis Tools
    - **Progress**: Core navigation and page structure complete
    """)
    
    # Roadmap
    st.subheader("🗺️ Project Roadmap")
    roadmap_data = {
        "Phase": ["1. Streamlit", "2. Airflow", "3. PostgreSQL", "4. dbt", "5. Analytics & LLM/RAG"],
        "Status": ["🟡 In Progress", "⚪ Pending", "⚪ Pending", "⚪ Pending", "⚪ Pending"],
        "Focus": [
            "Multi-page frontend UI",
            "Data pipeline orchestration",
            "Data warehouse & storage",
            "Analytics models & transformations",
            "Advanced analytics & AI integration"
        ]
    }
    
    df = pd.DataFrame(roadmap_data)
    st.table(df)
    
    # Getting Started
    st.subheader("🚀 Getting Started")
    st.write("""
    1. **Explore Data**: Use the Stock Overview page to browse available data
    2. **Analyze**: Visit the Analysis page to run custom queries
    3. **Chat**: Try the Assistant Chat for AI-powered insights
    4. **Monitor**: Check Indicators for real-time metrics
    5. **Manage**: Use Admin panel for system configuration
    """)
    

if __name__ == "__main__":
    main()
