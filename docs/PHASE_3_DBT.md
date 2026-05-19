# Phase 3: dbt Data Transformations

## Overview

Phase 3 teaches you how to:
- Set up dbt project for SQL transformations
- Create staging models (data cleaning)
- Create mart models (analytics layer)
- Test data quality
- Document your data

**Time to Complete:** 2-3 hours  
**Tech Stack:** dbt, PostgreSQL, Jinja2 SQL templating

**Prerequisites:** Complete Phase 2 (PostgreSQL with data)

---

## Learning Goals

- ✅ Understand dbt project structure and workflows
- ✅ Write dbt models in SQL
- ✅ Set up data lineage (staging → marts)
- ✅ Use dbt variables and macros
- ✅ Test models and validate data quality
- ✅ Document models and columns
- ✅ Run models against PostgreSQL

---

## Getting Started

### Step 1: Install dbt Packages

```bash
# Install Phase 3 (dbt) dependencies
uv sync --extra phase1 --extra phase2 --extra phase3

# Verify dbt installation
uv run dbt --version
```

**Expected Output:**
```
dbt 1.9.0+
dbt-core: 1.9.0
dbt-postgres: 1.0.0
dbt-duckdb: 1.9.0
```

### Step 2: Verify dbt Connection

```bash
# Navigate to dbt folder
cd dbt

# Test connection to PostgreSQL
uv run dbt debug --target prod

# Or test DuckDB (local)
uv run dbt debug --target dev
```

**Expected Output:**
```
All checks passed!
```

### Step 3: Install dbt Dependencies

```bash
# Download packages from packages.yml
uv run dbt deps
```

### Step 4: Run dbt Models

```bash
# Run against DuckDB (local testing)
uv run dbt run --target dev

# Run against PostgreSQL (production)
uv run dbt run --target prod
```

**Expected Output:**
```
Running with dbt 1.9.0
Found 2 models
Running 1/2 CREATE TABLE stg_prices
Running 2/2 CREATE TABLE fct_daily_prices
Done
```

### Step 5: Test Models

```bash
# Run dbt tests (if tests defined in .yml)
uv run dbt test
```

### Step 6: Generate Documentation

```bash
# Generate dbt docs
uv run dbt docs generate

# Serve docs locally (optional)
# uv run dbt docs serve --port 8001
```

---

## Key Concepts

### 1. dbt (Data Build Tool)

**What is dbt?**  
Framework for transforming raw data into analytical tables using SQL.

**Why dbt?**
- Version control for data transformations (like git for SQL)
- Test data quality
- Document data lineage
- Automate model rebuilding
- Collaborate on data work
- Industry standard (Airbnb, Netflix, DoorDash)

### 2. dbt Project Structure

```
dbt/
├── dbt_project.yml       # Project config
├── profiles.yml          # Database connections (targets)
├── packages.yml          # External packages
└── models/
    ├── sources.yml       # Source definitions (raw data)
    ├── staging/
    │   ├── stg_prices.sql
    │   └── stg_prices.yml
    └── marts/
        ├── fct_daily_prices.sql
        └── fct_technical_indicators.sql
```

### 3. Models Layer Architecture

**Staging Layer (`staging/`)**
- Clean and standardize raw data
- Remove duplicates, handle NULLs
- Simple transformations (case, rename columns)
- Select columns needed for downstream

**Mart Layer (`marts/`)**
- Business logic and aggregations
- Join multiple sources
- Create facts and dimensions
- Ready for analytics/BI

### 4. Model Definition (SQL + YAML)

**SQL Model** (`stg_prices.sql`):
```sql
SELECT
    symbol,
    timestamp,
    open,
    high,
    low,
    close,
    volume
FROM {{ source('raw', 'prices') }}
WHERE close IS NOT NULL
```

**YAML Documentation** (`stg_prices.yml`):
```yaml
version: 2

models:
  - name: stg_prices
    description: Cleaned price data
    columns:
      - name: symbol
        description: Stock symbol
        tests:
          - not_null
          - unique
```

### 5. Jinja2 Templating

dbt uses Jinja2 for dynamic SQL:

```sql
-- Reference another model
FROM {{ ref('stg_prices') }}

-- Reference source table
FROM {{ source('raw', 'prices') }}

-- Use variables
WHERE symbol IN ({{ var('symbols') }})

-- Conditional logic
{% if execute %}
    SELECT * FROM table WHERE 1=1
{% endif %}

-- Loops
{% for col in columns %}
    SELECT {{ col }} FROM table
{% endfor %}
```

### 6. Testing

dbt provides built-in tests:

```yaml
models:
  - name: stg_prices
    columns:
      - name: symbol
        tests:
          - not_null      # Column must not be NULL
          - unique        # All values must be unique
          - accepted_values:
              values: ['AAPL', 'MSFT', 'GOOGL']
      - name: close
        tests:
          - not_null
          - dbt_utils.relationships:  # Foreign key check
              to: ref('fct_daily_prices')
              field: close
```

**Run Tests:**
```bash
uv run dbt test
```

---

## TODO: Implement Phase 3 Models

### Staging Layer

**stg_prices.sql**
- [ ] Select from raw prices source
- [ ] Remove NULL values in critical columns
- [ ] Add calculated columns (pct_change, etc.)
- [ ] Order by symbol and timestamp

**stg_prices.yml**
- [ ] Document columns
- [ ] Add tests (not_null, unique on symbol+timestamp)
- [ ] Add data freshness check

### Mart Layer

**fct_daily_prices.sql**
- [ ] Aggregate 5-min prices to daily
- [ ] Calculate daily metrics: open, high, low, close, volume
- [ ] Add price changes (day-over-day % change)
- [ ] Join with other marts if needed

**fct_technical_indicators.sql**
- [ ] Calculate moving averages (SMA 20, 50, 200)
- [ ] Calculate RSI (Relative Strength Index)
- [ ] Calculate MACD (Moving Average Convergence Divergence)
- [ ] Calculate Bollinger Bands
- [ ] Add volume indicators

---

## dbt Commands Reference

```bash
# Parse and validate project
dbt parse

# Run models against target database
dbt run
dbt run --select stg_prices          # Run specific model
dbt run --models +fct_daily_prices   # Run model + dependencies
dbt run --exclude stg_prices         # Run all except one

# Test models
dbt test
dbt test --select stg_prices

# Generate documentation
dbt docs generate
dbt docs serve --port 8001           # View in browser

# Fresh run (drop and rebuild)
dbt run --full-refresh

# Debug (test connection)
dbt debug --target prod

# Compare targets (DuckDB vs PostgreSQL)
dbt run --target dev
dbt run --target prod
```

---

## profiles.yml Targets

Switch between targets for different environments:

```yaml
de_bootcamp:
  target: dev
  outputs:
    # Local development (DuckDB)
    dev:
      type: duckdb
      path: '../data/app.duckdb'
      schema: main
      threads: 4

    # Production (PostgreSQL)
    prod:
      type: postgres
      host: localhost
      user: postgres
      password: postgres
      port: 5432
      dbname: stocks
      schema: public
      threads: 4
```

**Use Specific Target:**
```bash
uv run dbt run --target dev      # DuckDB
uv run dbt run --target prod     # PostgreSQL
```

---

## Example: Complete dbt Model

**models/marts/fct_daily_prices.sql:**
```sql
{{ config(
    materialized='table',
    schema='marts'
) }}

SELECT
    symbol,
    DATE(timestamp) AS date,
    MIN(CAST(open AS FLOAT)) AS daily_open,
    MAX(CAST(high AS FLOAT)) AS daily_high,
    MIN(CAST(low AS FLOAT)) AS daily_low,
    MAX(CAST(close AS FLOAT)) AS daily_close,
    SUM(CAST(volume AS BIGINT)) AS daily_volume,
    ROUND(
        (MAX(CAST(close AS FLOAT)) - MIN(CAST(open AS FLOAT))) / 
        MIN(CAST(open AS FLOAT)) * 100, 
        2
    ) AS pct_change_daily
FROM {{ ref('stg_prices') }}
GROUP BY symbol, DATE(timestamp)
ORDER BY symbol, date DESC
```

**models/marts/fct_daily_prices.yml:**
```yaml
models:
  - name: fct_daily_prices
    description: Daily price aggregates
    columns:
      - name: symbol
        description: Stock symbol
        tests:
          - not_null
          - accepted_values:
              values: ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
      - name: date
        description: Date
        tests:
          - not_null
      - name: daily_close
        description: Daily closing price
        tests:
          - not_null
```

---

## Troubleshooting

### Issue: "dbt debug" fails with connection error
**Solution:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check credentials in profiles.yml
# Verify POSTGRES_URL in .env matches

# Test connection manually
docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c "SELECT 1"
```

### Issue: "ref() not found" error
**Solution:**
- Model name in SQL must match filename exactly
- Check spacing and quotes in YAML
- Run `dbt parse` to validate YAML syntax

### Issue: Models compile but create no output
**Solution:**
```bash
# Check if models are materialized correctly
dbt run --full-refresh

# Check target database
dbt run --target prod

# View generated SQL
dbt run --debug --target prod
```

### Issue: Test failures
**Solution:**
```bash
# Run tests in verbose mode
dbt test --debug

# Test specific model
dbt test --select stg_prices

# View test code
dbt test --select stg_prices --debug
```

---

## Next Steps After Phase 3

Once you're comfortable with:
- Writing dbt models
- Testing data quality
- Documenting data lineage
- Running transformations

You're ready for **Phase 4: Analytics & Dashboards**!

See [PHASE_4_ANALYTICS.md](PHASE_4_ANALYTICS.md)
