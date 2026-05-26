# Phase 1: Streamlit + yfinance

> 📊 **Implementation Status:** See [PROJECT_STATUS.md](PROJECT_STATUS.md) for current progress and pending tasks.

## Overview

Phase 1 teaches you how to:
- Pull live financial data from yfinance API
- Store data locally in DuckDB (embedded database, no setup needed)
- Display data in a Streamlit web app
- Explore and visualize data

**Time to Complete:** 1-2 hours  
**Tech Stack:** Python, yfinance, Streamlit, DuckDB, Plotly

---

## Learning Goals

- ✅ Understand yfinance API and what data is available
- ✅ Work with Pandas DataFrames for data manipulation
- ✅ Use DuckDB for embedded database storage (no PostgreSQL needed!)
- ✅ Build interactive Streamlit pages
- ✅ Create visualizations with Plotly
- ✅ Handle dates and timezones

---

## Getting Started

### Step 1: Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Install Phase 1 dependencies
uv sync --extra phase1
```

### Step 2: Test yfinance Connection

```bash
# Test that yfinance works
uv run python -c "
import yfinance as yf
data = yf.download('AAPL', period='5d', interval='5m')
print(f'Downloaded {len(data)} rows')
print(data.head())
"
```

**Expected Output:**
```
Downloaded 240 rows
                              Open     High      Low    Close      Volume
2026-05-13 09:30:00-04:00  189.50  189.75  189.40  189.60  12345600
...
```

### Step 3: Test DuckDB Connection

```bash
# Create and query a test table
uv run python -c "
import duckdb
conn = duckdb.connect('data/app.duckdb')
conn.execute('CREATE TABLE test (id INT, name VARCHAR)')
conn.execute('INSERT INTO test VALUES (1, \"test\")')
result = conn.execute('SELECT * FROM test').fetchall()
print(result)
conn.close()
"
```

**Expected:** `[(1, 'test')]`

### Step 4: Run Streamlit App

```bash
# Start the app
uv run streamlit run app/main.py

# Open browser to: http://localhost:8501
```

---

## Key Concepts

### 1. yfinance API

**What is yfinance?**  
Python library for downloading financial data from Yahoo Finance.

**Common Parameters:**
- `symbol`: Stock ticker (e.g., "AAPL", "MSFT", "BTC-USD")
- `interval`: Time interval (1m, 5m, 15m, 30m, 60m, 1h, 1d)
- `period`: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, max)
- `start`: Start date (YYYY-MM-DD)
- `end`: End date (YYYY-MM-DD)

**Example:**
```python
import yfinance as yf

# Download Apple 5-minute data for 5 days
data = yf.download('AAPL', period='5d', interval='5m')

# Download historical daily data
historical = yf.download('AAPL', start='2026-01-01', end='2026-05-18')
```

**DataFrame Columns:**
- `Open`: Opening price
- `High`: Highest price in period
- `Low`: Lowest price in period
- `Close`: Closing price
- `Volume`: Number of shares traded
- `Adj Close`: Adjusted closing price (rarely used)

### 2. DuckDB

**What is DuckDB?**  
Embedded SQL database (no server needed). Stores data in a local file (`data/app.duckdb`).

**Why DuckDB for Phase 1?**
- No setup (unlike PostgreSQL)
- Perfect for learning
- Fast queries on local data
- ACID compliant

**Basic Operations:**
```python
import duckdb

# Connect to DuckDB
conn = duckdb.connect('data/app.duckdb')

# Create table
conn.execute('''
    CREATE TABLE IF NOT EXISTS prices (
        symbol VARCHAR,
        timestamp TIMESTAMP,
        open FLOAT,
        high FLOAT,
        low FLOAT,
        close FLOAT,
        volume BIGINT
    )
''')

# Insert data
conn.execute('''
    INSERT INTO prices VALUES ('AAPL', NOW(), 189.5, 189.8, 189.4, 189.6, 1000000)
''')

# Query data
result = conn.execute('SELECT * FROM prices WHERE symbol = "AAPL"').fetchall()
print(result)

# Close connection
conn.close()
```

### 3. Streamlit

**What is Streamlit?**  
Python framework for building data apps in minutes. No HTML/CSS/JavaScript needed!

**Multi-Page Apps:**
```python
import streamlit as st

# Create pages (files in app/views/ folder)
pages = {
    "Home": "app/views/01_Home_Dashboard.py",
    "Stock Overview": "app/views/02_Stock_Overview.py",
    "Data Explorer": "app/views/03_Data_Explorer.py",
}

st.set_page_config(page_title="My App")
# Page routing here
```

**Common Streamlit Components:**
```python
st.title("My App")           # Title
st.subheader("Section")      # Subheading
st.write("Hello world")      # Text output
st.dataframe(df)             # Display DataFrame
st.metric("AAPL", 189.50)   # Show KPI
st.selectbox("Symbol", ["AAPL", "MSFT"])  # Dropdown
st.date_input("Date")        # Date picker
st.button("Click me")        # Button
st.slider("Value", 0, 100)   # Slider
st.text_input("Name")        # Text input
st.plotly_chart(fig)         # Plotly chart
```

### 4. Plotly

**What is Plotly?**  
Interactive visualization library. Works seamlessly with Streamlit.

**Common Charts:**
```python
import plotly.graph_objects as go
import plotly.express as px

# Line chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['date'], y=df['close'], mode='lines'))
st.plotly_chart(fig)

# Candlestick chart (for OHLC data)
fig = go.Figure(data=[go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close']
)])
st.plotly_chart(fig)
```

---

## TODO: Implement Phase 1 Pages

### 1. Home Dashboard (01_Home_Dashboard.py)
- [ ] Welcome message and project overview
- [ ] Quick stats (# of symbols, last update time, total data points)
- [ ] Navigation guide to other pages
- [ ] Getting started instructions

### 2. Stock Overview (02_Stock_Overview.py)
- [ ] Symbol selector (dropdown or multiselect)
- [ ] Date range picker
- [ ] Load data from yfinance using symbol + date range
- [ ] Display Plotly candlestick chart
- [ ] Show OHLCV table below chart
- [ ] Add refresh button to reload data

### 3. Data Explorer (03_Data_Explorer.py)
- [ ] Symbol and date range filters
- [ ] Display raw price data in table format
- [ ] Show summary statistics (min, max, mean, std)
- [ ] Export data to CSV button
- [ ] Search/filter capability

### 4. Admin (99_Admin.py)
- [ ] Manual data refresh button
- [ ] Database status (check DuckDB file size, row count)
- [ ] Clear cache button
- [ ] View recent errors or logs
- [ ] Configuration editor (edit symbols.toml)

---

## Resources

- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Plotly Charts](https://plotly.com/python/)
- [DuckDB Docs](https://duckdb.org/docs/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'streamlit'"
**Solution:** Run `uv sync --extra phase1`

### Issue: "No module named 'yfinance'"
**Solution:** Run `uv sync --extra phase1`

### Issue: yfinance returns empty data
**Solution:** Check date ranges are valid and symbol exists (e.g., "AAPL", not "apple")

### Issue: DuckDB "file is locked"
**Solution:** Make sure no other process has the database open. Close any other Python shells or Streamlit instances.

### Issue: Streamlit app won't start on port 8501
**Solution:** Port may be in use. Kill the process: `lsof -i :8501 | grep LISTEN | awk '{print $2}' | xargs kill -9`

---

## Next Steps After Phase 1

Once you're comfortable with:
- Downloading yfinance data
- Storing in DuckDB
- Building Streamlit pages

You're ready for **Phase 2: Apache Airflow + PostgreSQL**!

See [PHASE_2_AIRFLOW_POSTGRES.md](PHASE_2_AIRFLOW_POSTGRES.md)
