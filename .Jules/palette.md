## 2026-05-20 - Streamlit Async Operations Loading State
**Learning:** Streamlit buttons don't have native loading states built-in like web buttons, making it hard for users to know if an action was registered when fetching remote data (e.g., from yfinance).
**Action:** Always wrap data fetching calls triggered by `st.button` in an `st.spinner()` block to provide immediate visual feedback.
