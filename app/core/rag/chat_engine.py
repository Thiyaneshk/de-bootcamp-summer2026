"""
Phase 5: LLM + RAG Chat Engine

Structured RAG pipeline to retrieve price and technical indicator context from
PostgreSQL database and answer financial questions using a local Ollama LLM.
"""

import logging
import re

import ollama
import pandas as pd
from sqlalchemy import text

from app.config import AppConfig
from app.db.connection import get_postgres_engine

logger = logging.getLogger(__name__)


def get_ollama_response(prompt: str, model: str = "mistral") -> str:
    """
    Get response from local Ollama LLM.
    """
    try:
        response = ollama.generate(model=model, prompt=prompt)
        return response.get("response", "No response returned from model.")
    except Exception as e:
        logger.error("Ollama generate failed: %s", e)
        return f"Error calling Ollama model '{model}': {e}"


def _get_prices_context(sym: str, days_limit: int, engine) -> str | None:
    price_query = """
        SELECT date, daily_open, daily_high, daily_low, daily_close, daily_volume
        FROM public_marts.fct_daily_prices
        WHERE symbol = :symbol
        ORDER BY date DESC
        LIMIT :limit
    """
    df_prices = pd.read_sql(
        text(price_query),
        engine,
        params={"symbol": sym, "limit": days_limit},
    )
    if not df_prices.empty:
        # Reverse to show chronological order
        df_prices = df_prices.iloc[::-1]
        for col in ["daily_open", "daily_high", "daily_low", "daily_close"]:
            df_prices[col] = df_prices[col].round(2)
        return (
            f"### {sym} Price History (Last {len(df_prices)} trading days):\n"
            + df_prices.to_markdown(index=False)
        )
    return None


def _get_indicators_context(sym: str, days_limit: int, engine) -> str | None:
    ind_query = """
        SELECT DATE(timestamp) as date, close, sma_20, sma_50, ema_50, ema_200
        FROM public_marts.fct_technical_indicators
        WHERE symbol = :symbol
        ORDER BY timestamp DESC
        LIMIT :limit
    """
    df_ind = pd.read_sql(
        text(ind_query),
        engine,
        params={"symbol": sym, "limit": days_limit},
    )
    if not df_ind.empty:
        df_ind = df_ind.iloc[::-1]
        for col in ["close", "sma_20", "sma_50", "ema_50", "ema_200"]:
            df_ind[col] = df_ind[col].round(2)
        return (
            f"### {sym} Technical Indicators (Last {len(df_ind)} trading days):\n"
            + df_ind.to_markdown(index=False)
        )
    return None


def _get_snapshot_context(engine) -> str | None:
    snapshot_query = """
        WITH latest_date AS (
            SELECT MAX(date) as max_date FROM public_marts.fct_daily_prices
        )
        SELECT symbol, date, daily_open, daily_high, daily_low, daily_close, daily_volume
        FROM public_marts.fct_daily_prices
        WHERE date = (SELECT max_date FROM latest_date)
        ORDER BY symbol
    """
    df_snapshot = pd.read_sql(text(snapshot_query), engine)
    if not df_snapshot.empty:
        for col in ["daily_open", "daily_high", "daily_low", "daily_close"]:
            df_snapshot[col] = df_snapshot[col].round(2)
        return (
            "### Latest Market Price Snapshot (All Active Tickers):\n"
            + df_snapshot.to_markdown(index=False)
        )
    return None


def _get_volatility_context(engine) -> str | None:
    vol_query = """
        SELECT
            symbol,
            COUNT(daily_close) as data_points,
            MIN(daily_close) as min_price,
            MAX(daily_close) as max_price,
            ROUND(STDDEV(daily_close)::numeric, 2) as volatility_stddev
        FROM public_marts.fct_daily_prices
        GROUP BY symbol
        ORDER BY symbol
    """
    df_vol = pd.read_sql(text(vol_query), engine)
    if not df_vol.empty:
        return "### Historical Price Ranges & Volatility:\n" + df_vol.to_markdown(
            index=False
        )
    return None


def retrieve_context(query: str, days_limit: int = 10) -> str:
    """
    Retrieve relevant financial data context from PostgreSQL based on query keywords.
    """
    config = AppConfig()
    all_symbols = config.symbols

    # Identify which symbols are mentioned in the query
    mentioned = []
    for sym in all_symbols:
        # Tickers can contain dots (e.g. ITC.NS), handle escaping safely
        pattern = r"\b" + re.escape(sym) + r"\b"
        if re.search(pattern, query, re.IGNORECASE):
            mentioned.append(sym)

    context_parts = []

    try:
        with get_postgres_engine() as engine:
            if mentioned:
                # Retrieve price and indicator history for each mentioned symbol
                for sym in mentioned:
                    prices_ctx = _get_prices_context(sym, days_limit, engine)
                    if prices_ctx:
                        context_parts.append(prices_ctx)

                    indicators_ctx = _get_indicators_context(sym, days_limit, engine)
                    if indicators_ctx:
                        context_parts.append(indicators_ctx)
            else:
                # If no specific symbol is mentioned, load the latest snapshot for all symbols
                snapshot_ctx = _get_snapshot_context(engine)
                if snapshot_ctx:
                    context_parts.append(snapshot_ctx)

                # Also pull volatility summary to aid comparisons
                volatility_ctx = _get_volatility_context(engine)
                if volatility_ctx:
                    context_parts.append(volatility_ctx)

    except Exception as e:
        logger.error("RAG context retrieval failed: %s", e)
        context_parts.append(f"Error retrieving database context: {e}")

    return (
        "\n\n".join(context_parts)
        if context_parts
        else "No relevant database data found."
    )


def chat_with_rag(
    query: str, model: str = "mistral", chat_history: list = None, days_limit: int = 10
) -> dict:
    """
    Main RAG chat entry point. Combines query context, rules, and history.
    """
    if chat_history is None:
        chat_history = []

    # 1. Retrieve data context
    context = retrieve_context(query, days_limit=days_limit)

    # 2. Build system instructions
    system_prompt = f"""You are Antigravity, a professional financial analyst AI assistant.
You have access to historical stock prices and computed moving averages (SMA 20, SMA 50, EMA 50, EMA 200) stored in a PostgreSQL database.

Your task is to analyze the retrieved database context and answer user queries accurately.
Always follow these guidelines:
1. Rely primarily on the RETRIEVED DATABASE CONTEXT below for all numbers, prices, dates, and trends.
2. If the user asks about topics or symbols not covered in the context, clearly state that you do not have access to that data.
3. Be analytical: cite specific prices, dates, or crossover events from the data context to support your statements.
4. Keep answers clear, structured, and concise.

RETRIEVED DATABASE CONTEXT:
{context}
"""

    # 3. Construct chat messages array for Ollama Chat API
    messages = [{"role": "system", "content": system_prompt}]

    # Append sliding window of memory (last 6 messages)
    for msg in chat_history[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Append the current query
    messages.append({"role": "user", "content": query})

    try:
        # Call Ollama Chat API
        response = ollama.chat(model=model, messages=messages)
        answer = response.message.content

        return {"response": answer, "data_context": context, "model": model}
    except Exception as e:
        logger.error("Ollama chat failed: %s", e)
        error_msg = (
            f"❌ Error communicating with Ollama model '{model}': {e}\n\n"
            "**Troubleshooting Checklist:**\n"
            "1. Make sure Ollama is running (`bash scripts/init_ollama.sh`)\n"
            "2. Confirm the selected model is pulled on your system"
        )
        return {"response": error_msg, "data_context": context, "model": model}
