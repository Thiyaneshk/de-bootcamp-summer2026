# Phase 4: Analytics & Dashboards

> 📊 **Implementation Status:** See [PROJECT_STATUS.md](PROJECT_STATUS.md) for current progress and pending tasks.

## Overview

Phase 4 teaches you how to:
- Query dbt-generated data marts
- Create analytics dashboards in Streamlit
- Analyze stock performance and technical indicators
- Build interactive visualizations
- Answer business questions with data

**Time to Complete:** 1-2 hours  
**Tech Stack:** Streamlit, SQL, Plotly, PostgreSQL

**Prerequisites:** Complete Phase 3 (dbt models running)

---

## Learning Goals

- ✅ Write efficient SQL queries on dbt marts
- ✅ Create Streamlit dashboards with KPIs
- ✅ Build interactive charts and filters
- ✅ Analyze stock performance metrics
- ✅ Visualize technical indicators
- ✅ Use Streamlit caching for performance

---

## Getting Started

### Step 1: Ensure dbt Models are Built

```bash
# Run dbt models against PostgreSQL
cd dbt
uv run dbt run --target prod

# Verify models were created
docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c "\dt public.*"
```

**Expected Tables:**
- `stg_prices` (staging schema)
- `fct_daily_prices` (marts schema)
- `fct_technical_indicators` (marts schema)

### Step 2: Verify Data in Marts

```bash
# Query daily prices
docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c "
    SELECT symbol, date, daily_close, pct_change_daily 
    FROM public.fct_daily_prices 
    LIMIT 10
"
```

### Step 3: Run Updated Streamlit App

```bash
# Update .env to use PostgreSQL
export POSTGRES_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/stocks"

# Run Streamlit
uv run streamlit run app/main.py

# Navigate to Indicators page (04_Indicators.py)
```

---

## Key Concepts

### 1. Analytics Queries on dbt Marts

**Pattern: Query dbt Marts Instead of Raw Data**

```python
import pandas as pd
from sqlalchemy import create_engine

# Connect to PostgreSQL
engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost:5432/stocks")

# Query dbt mart instead of raw data
query = """
    SELECT symbol, date, daily_open, daily_close, daily_volume
    FROM public.fct_daily_prices
    WHERE symbol = %s
    ORDER BY date DESC
    LIMIT 30
"""

df = pd.read_sql(query, engine, params=('AAPL',))
```

### 2. Common Analytics Queries

**Top Performers (Price Change)**
```sql
SELECT 
    symbol, 
    date,
    daily_close,
    pct_change_daily,
    ROW_NUMBER() OVER (ORDER BY pct_change_daily DESC) AS rank
FROM fct_daily_prices
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY pct_change_daily DESC
LIMIT 10
```

**Moving Average Crossover**
```sql
SELECT 
    symbol,
    date,
    daily_close,
    sma_20,
    sma_50,
    CASE 
        WHEN sma_20 > sma_50 THEN 'Bullish'
        WHEN sma_20 < sma_50 THEN 'Bearish'
        ELSE 'Neutral'
    END AS signal
FROM fct_technical_indicators
ORDER BY symbol, date DESC
```

**Volatility Analysis**
```sql
SELECT 
    symbol,
    DATE_TRUNC('week', date) AS week,
    STDDEV(pct_change_daily) AS volatility,
    AVG(daily_volume) AS avg_volume
FROM fct_daily_prices
GROUP BY symbol, DATE_TRUNC('week', date)
ORDER BY symbol, week DESC
```

### 3. Streamlit Performance Optimization

**Caching Query Results**

```python
import streamlit as st
from functools import lru_cache

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_daily_prices(symbol):
    """Cache query results to avoid repeated database hits."""
    query = f"SELECT * FROM fct_daily_prices WHERE symbol = '{symbol}'"
    return pd.read_sql(query, engine)

# Use cached function
df = get_daily_prices('AAPL')
```

**Session State for Filters**

```python
import streamlit as st

# Store selected symbol in session state
if 'selected_symbol' not in st.session_state:
    st.session_state.selected_symbol = 'AAPL'

# Dropdown updates session state
symbol = st.selectbox(
    'Select Symbol',
    ['AAPL', 'MSFT', 'GOOGL'],
    index=['AAPL', 'MSFT', 'GOOGL'].index(st.session_state.selected_symbol)
)
st.session_state.selected_symbol = symbol
```

---

## TODO: Implement Phase 4 Pages

### Analytics Dashboard (05_Analysis.py)

- [ ] **KPI Cards**
  - Current price for selected symbol
  - 7-day % change
  - 30-day high and low
  - Average daily volume

- [ ] **Performance Chart**
  - Line chart of daily closing prices
  - Date range picker (1M, 3M, 6M, 1Y)
  - Comparison of multiple symbols

- [ ] **Technical Indicators Chart**
  - Moving averages (SMA 20, 50, 200)
  - Display on same chart as price
  - Toggle indicators on/off

- [ ] **Correlation Analysis**
  - Heatmap of price correlations between symbols
  - Update based on selected date range

- [ ] **Volatility Metrics**
  - Historical volatility (30-day std dev)
  - Compare volatility across symbols
  - Bar chart

- [ ] **Volume Analysis**
  - Average daily volume by symbol
  - Volume trend over time
  - Identify unusual volume spikes

### Indicators Page (04_Indicators.py)

- [ ] **Signal Table**
  - Display technical signals (Bullish/Bearish)
  - RSI values
  - MACD signals
  - Filter by symbol or signal type

- [ ] **Pattern Recognition**
  - Identify moving average crossovers
  - Flag extreme RSI values (oversold/overbought)
  - Show support/resistance levels

---

## SQL Analytics Queries Library

### Performance Metrics

```sql
-- Monthly performance summary
SELECT 
    symbol,
    DATE_TRUNC('month', date) AS month,
    FIRST_VALUE(daily_open) OVER (PARTITION BY symbol, DATE_TRUNC('month', date) ORDER BY date) AS month_open,
    LAST_VALUE(daily_close) OVER (PARTITION BY symbol, DATE_TRUNC('month', date) ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS month_close,
    MIN(daily_low) AS month_low,
    MAX(daily_high) AS month_high,
    ROUND(SUM(daily_volume) / 1000000, 2) AS volume_millions
FROM fct_daily_prices
GROUP BY symbol, DATE_TRUNC('month', date)
ORDER BY symbol, month DESC
```

### Trend Detection

```sql
-- Recent trend (last 20 days average vs 50 days average)
SELECT 
    symbol,
    ROUND(AVG(daily_close) FILTER (WHERE date >= CURRENT_DATE - INTERVAL '20 days'), 2) AS avg_20d,
    ROUND(AVG(daily_close) FILTER (WHERE date >= CURRENT_DATE - INTERVAL '50 days'), 2) AS avg_50d,
    CASE 
        WHEN AVG(daily_close) FILTER (WHERE date >= CURRENT_DATE - INTERVAL '20 days') > 
             AVG(daily_close) FILTER (WHERE date >= CURRENT_DATE - INTERVAL '50 days')
        THEN 'Uptrend'
        ELSE 'Downtrend'
    END AS trend
FROM fct_daily_prices
GROUP BY symbol
```

### Correlation Matrix

```sql
-- Prepare data for correlation heatmap
SELECT 
    a.symbol AS symbol_a,
    b.symbol AS symbol_b,
    CORR(a.pct_change_daily, b.pct_change_daily) AS correlation
FROM fct_daily_prices a
JOIN fct_daily_prices b 
    ON DATE(a.timestamp) = DATE(b.timestamp)
    AND a.symbol < b.symbol  -- Avoid duplicates
WHERE a.date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY a.symbol, b.symbol
ORDER BY a.symbol, b.symbol
```

---

## Streamlit Dashboard Best Practices

### 1. Layout & Organization

```python
import streamlit as st

# Wide layout for more space
st.set_page_config(layout="wide")

# Create columns for side-by-side elements
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current Price", "$189.50", "↑ 2.5%")
with col2:
    st.metric("Volume", "50.2M", "↓ 3.1%")
with col3:
    st.metric("P/E Ratio", "28.5", "→")

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["Price", "Indicators", "Correlation"])
with tab1:
    st.plotly_chart(price_chart)
```

### 2. Efficient Queries

```python
import streamlit as st

# Query only needed columns
@st.cache_data(ttl=3600)
def get_daily_prices(symbol: str, days: int = 365):
    query = f"""
        SELECT date, daily_open, daily_close, daily_volume
        FROM fct_daily_prices
        WHERE symbol = %s AND date >= CURRENT_DATE - INTERVAL '{days} days'
        ORDER BY date
    """
    return pd.read_sql(query, engine, params=(symbol,))

# Use parameterized queries to prevent SQL injection
```

### 3. Interactive Filters

```python
import streamlit as st

# Multi-select for multiple symbols
symbols = st.multiselect(
    'Select Symbols',
    ['AAPL', 'MSFT', 'GOOGL', 'TSLA'],
    default=['AAPL']
)

# Date range picker
date_range = st.date_input("Date Range", [pd.Timestamp('2026-01-01')])

# Slider for moving averages
ma_window = st.slider("Moving Average Window", 5, 200, 50)
```

---

## Visualization Examples

### Line Chart with Moving Averages

```python
import plotly.graph_objects as go

fig = go.Figure()

# Add price line
fig.add_trace(go.Scatter(
    x=df['date'],
    y=df['daily_close'],
    mode='lines',
    name='Close Price',
    line=dict(color='blue')
))

# Add SMA 20
fig.add_trace(go.Scatter(
    x=df['date'],
    y=df['sma_20'],
    mode='lines',
    name='SMA 20',
    line=dict(color='orange', dash='dash')
))

fig.update_layout(
    title='Price with Moving Averages',
    xaxis_title='Date',
    yaxis_title='Price ($)',
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)
```

### Volume Chart

```python
fig = go.Figure(data=[
    go.Bar(x=df['date'], y=df['daily_volume'], name='Volume')
])
fig.update_layout(title='Trading Volume')
st.plotly_chart(fig, use_container_width=True)
```

### Heatmap (Correlation)

```python
import plotly.express as px

fig = px.imshow(
    correlation_matrix,
    labels=dict(x="Symbol", y="Symbol", color="Correlation"),
    title="Symbol Correlation Matrix"
)
st.plotly_chart(fig, use_container_width=True)
```

---

## Troubleshooting

### Issue: Dashboard page loads slowly
**Solution:**
- Add `@st.cache_data` decorator to query functions
- Increase TTL (cache time-to-live)
- Optimize SQL queries (add indexes, limit rows)
- Use `st.session_state` to avoid re-running filters

### Issue: "No connection to database"
**Solution:**
- Verify PostgreSQL is running: `docker-compose ps postgres`
- Check POSTGRES_URL in .env
- Test connection: `docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c "SELECT 1"`

### Issue: Charts not displaying
**Solution:**
- Check query returns data: `df.head()`
- Verify Plotly is installed: `uv pip list | grep plotly`
- Check for missing values: `df.isnull().sum()`

---

## Next Steps After Phase 4

Once you're comfortable with:
- Writing analytics SQL queries
- Building Streamlit dashboards
- Visualizing data with Plotly
- Creating interactive filters

You're ready for **Phase 5: LLM + RAG Integration** (optional)!

See [PHASE_5_LLM_RAG.md](PHASE_5_LLM_RAG.md)

---

**Congrats!** You now have a complete data analytics stack! 🎉
