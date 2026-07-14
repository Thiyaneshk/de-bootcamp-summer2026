"""
Phase 5: AI Analyst Chat Page

Interactive Chat Interface using Streamlit conversational UI and RAG over
PostgreSQL database tables.
"""

try:
    import ollama
except (ImportError, ModuleNotFoundError):
    ollama = None

import streamlit as st

from app.core.rag.chat_engine import chat_with_rag


def get_available_models() -> list[str]:
    """Dynamically query Ollama for installed models, with fallbacks."""
    if ollama is None:
        return ["gemma4:latest", "mistral"]

    try:
        models_data = ollama.list()
        names = [m.model for m in models_data.models]
        if names:
            return names
    except Exception:
        pass
    return ["gemma4:latest", "mistral"]  # Fallbacks if Ollama is unreachable


def main():
    """AI analyst chat page."""

    st.markdown(
        """
        <div style="
            background:linear-gradient(135deg,#1e1b4b 0%,#311042 100%);
            border:1px solid #4c1d95;border-radius:14px;
            padding:22px 24px 16px;margin-bottom:20px
        ">
            <h2 style="margin:0;color:#f3e8ff">🤖 AI Financial Analyst</h2>
            <p style="color:#d8b4fe;margin:6px 0 0;font-size:0.92rem">
                Ask natural language questions grounded in database price records and technical indicator moving averages
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Sidebar Settings ──────────────────────────────────────────────────────
    st.sidebar.markdown("### ⚙️ Analyst Configuration")

    models = get_available_models()
    selected_model = st.sidebar.selectbox(
        "Select LLM Model",
        options=models,
        index=0,
        help="Models currently pulled in your Ollama installation",
    )

    context_days = st.sidebar.slider(
        "Context History (Days)",
        min_value=3,
        max_value=30,
        value=10,
        help="Number of historical price/indicator records to fetch for mentioned symbols",
    )

    if st.sidebar.button("🧹 Clear Chat History", type="secondary"):
        st.session_state.chat_history = []
        st.success("Chat history cleared!")
        st.rerun()

    # ── Quick Presets ────────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💡 Sample Questions")

    preset_query = None
    if st.sidebar.button("📈 Latest market snapshot"):
        preset_query = "Give me a summary of the latest close price and volume for all stocks in the database."
    if st.sidebar.button("⚡ Volatility profile checks"):
        preset_query = "Which stock has the highest historical volatility in the database, and what is its range?"
    if st.sidebar.button("🔍 AAPL technical crossover check"):
        preset_query = "What is the recent price trend of AAPL? Check if it is above or below its SMA 20, SMA 50, and EMA 200."
    if st.sidebar.button("📊 Compare MSFT vs GOOGL close"):
        preset_query = "Compare the recent daily close prices of MSFT and GOOGL. Which has been performing better over the last few days?"

    # ── Conversational Logs ──────────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display welcome message if history is empty
    if not st.session_state.chat_history:
        with st.chat_message("assistant"):
            st.markdown("""
                Hello! I am **Antigravity**, your local AI Financial Analyst.
                I have real-time access to the PostgreSQL database schemas containing raw prices, staging models, and dbt indicator tables.

                You can ask me questions like:
                * *'What was the close price of AAPL over the last 5 days?'*
                * *'Is MSFT currently in a bullish or bearish moving average phase?'*
                * *'Are there any technical indicators or volatility spikes on LUPIN.NS?'*

                How can I assist your market research today?
                """)

    # Render previous logs
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            # If there is data context saved with the assistant message, render it in an expander
            if message["role"] == "assistant" and "data_context" in message:
                with st.expander("📊 Retained SQL context for this response"):
                    st.code(message["data_context"], language="markdown")

    # Get user prompt (either text input or preset button click)
    user_input = st.chat_input("Ask about stock data...")
    query = user_input or preset_query

    # ── Process Query ────────────────────────────────────────────────────────
    if query:
        # Append user message
        st.session_state.chat_history.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        # Get response from chat engine
        with st.chat_message("assistant"):
            with st.spinner("Analyzing PostgreSQL data and thinking..."):
                result = chat_with_rag(
                    query=query,
                    model=selected_model,
                    chat_history=st.session_state.chat_history[
                        :-1
                    ],  # pass previous history
                    days_limit=context_days,
                )

            response_text = result["response"]
            data_context = result["data_context"]

            st.write(response_text)

            # Show SQL context
            if data_context:
                with st.expander("📊 Retained SQL context for this response"):
                    st.code(data_context, language="markdown")

        # Append assistant message with context
        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": response_text,
                "data_context": data_context,
            }
        )


if __name__ == "__main__":
    main()
