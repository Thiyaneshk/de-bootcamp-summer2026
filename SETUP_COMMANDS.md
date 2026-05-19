# Complete Setup Commands: de-bootcamp-summer2026

This document contains **every command** needed to create, setup, and run the project from start to finish. Follow sequentially for Phase 0 through Phase 5.

---

## ⚙️ Phase 0: Repository & Environment Setup

### Step 0.1: Create Local Repository

```bash
# Create project directory
mkdir -p ~/Documents/GitHub/stock-ml/de-bootcamp-summer2026
cd ~/Documents/GitHub/stock-ml/de-bootcamp-summer2026

# Initialize git repository
git init

# Add .gitignore, README, pyproject.toml, etc. (via scaffold)
# (Files already provided in scaffold)

# Initial commit
git add .
git commit -m "Initial commit: project scaffold"
```

### Step 0.2: Create Remote Repository on GitHub

```bash
# Go to GitHub and:
# 1. Create new repository: https://github.com/new
#    Name: de-bootcamp-summer2026
#    Description: Data Engineering Learning Project
#    Add README, .gitignore (or let local files take precedence)
#    Do NOT initialize with README.md to avoid conflicts
#
# 2. Copy the repository URL from GitHub (HTTPS or SSH)

# Add remote and push (replace URL with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/de-bootcamp-summer2026.git
git branch -M main
git push -u origin main
```

### Step 0.3: Install uv (Fast Python Package Manager)

```bash
# Install uv (one-time setup)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version

# Add uv to PATH (if not done automatically)
export PATH="$HOME/.cargo/bin:$PATH"
```

### Step 0.4: Setup Python Environment

```bash
# Navigate to project directory (if not already there)
cd ~/Documents/GitHub/stock-ml/de-bootcamp-summer2026

# Create .env file from template
cp .env.example .env

# Edit .env if needed (optional for Phase 1)
# nano .env  # or your favorite editor

# Verify Python version (should be 3.11+)
python3 --version
```

### Step 0.5: Install Phase 1 Dependencies

```bash
# Use uv to sync Phase 1 dependencies
uv sync --extra phase1

# Alternative: Install all phases (for Docker)
# uv sync --extra all

# Verify installation
uv pip list | grep streamlit
```

**Expected output:** Streamlit version ≥1.40.0 and yfinance should be listed.

---

## 🎨 Phase 1: Streamlit + yfinance (Local Development)

### Step 1.1: Test yfinance Data Loading

```bash
# Run a quick test to verify yfinance works
uv run python -c "
import yfinance as yf
data = yf.download('AAPL', period='5d', interval='5m')
print(f'Downloaded {len(data)} rows')
print(data.head())
"
```

**Expected:** Should print AAPL price data with 5-minute intervals.

### Step 1.2: Verify DuckDB Setup

```bash
# Test DuckDB connection
uv run python -c "
import duckdb
conn = duckdb.connect('data/app.duckdb')
print('DuckDB connection successful')
conn.execute('CREATE TABLE IF NOT EXISTS test (id INT, name VARCHAR)')
conn.execute('INSERT INTO test VALUES (1, \"test\")')
result = conn.execute('SELECT * FROM test').fetchall()
print(result)
conn.close()
"
```

**Expected:** Should print `[(1, 'test')]` and create `data/app.duckdb` file.

### Step 1.3: Run Streamlit App (Local)

```bash
# Start the Streamlit development server
uv run streamlit run app/main.py

# App will open at: http://localhost:8501
# Press Ctrl+C to stop
```

**Expected:** 
- Streamlit server starts on port 8501
- Browser opens to `http://localhost:8501`
- Home page loads (even if empty - it's a scaffold!)

### Step 1.4: Test Data Loading & Storage

```bash
# In another terminal, test the ETL pipeline
uv run python -c "
from app.core.etl.prices import load_prices_5m
from app.db.connection import get_duckdb_connection

# Load data
prices = load_prices_5m('AAPL', start_date='2026-05-13')
print(f'Loaded {len(prices)} rows')

# Store in DuckDB
conn = get_duckdb_connection()
conn.execute('''
    CREATE TABLE IF NOT EXISTS prices (
        symbol VARCHAR,
        open FLOAT,
        high FLOAT,
        low FLOAT,
        close FLOAT,
        volume BIGINT,
        timestamp TIMESTAMP
    )
''')
# Insert logic would go here
"
```

### Step 1.5: Verify Phase 1 is Working

```bash
# Check that all Phase 1 files exist
ls -la app/main.py
ls -la app/core/etl/prices.py
ls -la app/db/connection.py
ls -la config/symbols.toml

# Check data folder created
ls -la data/
```

**Phase 1 Checkpoint:** ✅ Streamlit runs locally, yfinance data loads, DuckDB stores data

---

## 🚂 Phase 2: Apache Airflow + PostgreSQL

### Step 2.1: Install Phase 2 Dependencies

```bash
# Add Phase 2 (Airflow) dependencies
uv sync --extra phase1 --extra phase2

# Verify Airflow installation
uv run airflow version
```

**Expected:** Should show Apache Airflow version 2.10.2+

### Step 2.2: Start PostgreSQL with Docker

```bash
# Start only PostgreSQL service
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
sleep 5

# Verify PostgreSQL is running
docker-compose ps

# Connect to PostgreSQL and verify
docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c "SELECT version();"
```

**Expected:** PostgreSQL version 15 info should be displayed.

### Step 2.3: Initialize PostgreSQL Schema

```bash
# Create database schema
uv run python scripts/init_db.py

# Verify tables were created
docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c "\dt"
```

**Expected:** Should see tables like `prices`, `watchlist`, etc. (if implemented).

### Step 2.4: Set PostgreSQL in Environment

```bash
# Update .env to use PostgreSQL instead of DuckDB
# Edit .env and uncomment the POSTGRES_URL line:
# POSTGRES_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/stocks

# Or set via shell (temporary)
export POSTGRES_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/stocks"
```

### Step 2.5: Initialize Airflow

```bash
# Set Airflow home directory
export AIRFLOW_HOME=$(pwd)/airflow
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/airflow/dags

# Initialize Airflow database
uv run airflow db init

# Create Airflow admin user (interactive)
uv run airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com

# Or non-interactive:
# uv run airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com
```

**Expected:** Airflow SQLite database created at `airflow/airflow.db`.

### Step 2.6: Start Airflow Services

```bash
# Terminal 1: Start Airflow scheduler (background process)
export AIRFLOW_HOME=$(pwd)/airflow
export AIRFLOW__CORE__LOAD_EXAMPLES=False
uv run airflow scheduler

# Terminal 2: Start Airflow webserver (in new terminal)
export AIRFLOW_HOME=$(pwd)/airflow
uv run airflow webserver --port 8080

# Airflow UI: http://localhost:8080
# Login: admin / admin
```

### Step 2.7: Verify DAGs are Loaded

```bash
# In another terminal, list available DAGs
export AIRFLOW_HOME=$(pwd)/airflow
uv run airflow dags list

# Should show: etl_prices_dag, example_placeholder_dag
```

**Expected:** DAGs appear in Airflow UI at `http://localhost:8080`.

### Step 2.8: Trigger ETL DAG

```bash
# Manually trigger the ETL DAG
export AIRFLOW_HOME=$(pwd)/airflow
uv run airflow dags trigger etl_prices_dag

# Monitor DAG execution in Airflow UI or CLI
uv run airflow dags list-runs --dag-id etl_prices_dag
```

### Step 2.9: Verify Data in PostgreSQL

```bash
# Check if data was inserted
docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c "SELECT * FROM prices LIMIT 5;"

# Count rows
docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c "SELECT COUNT(*) FROM prices;"
```

**Phase 2 Checkpoint:** ✅ PostgreSQL running, Airflow DAGs execute, data flows into database

---

## 🔄 Phase 3: dbt Data Transformations

### Step 3.1: Install dbt Packages

```bash
# Add Phase 3 (dbt) dependencies
uv sync --extra phase1 --extra phase2 --extra phase3

# Verify dbt installation
uv run dbt --version
```

**Expected:** dbt-core, dbt-postgres, dbt-duckdb versions displayed.

### Step 3.2: Initialize dbt Project (if not scaffolded)

```bash
# Navigate to dbt directory
cd dbt

# dbt profiles.yml should already be configured
# Verify profiles are accessible
uv run dbt debug --target dev

# Should show "All checks passed!" and profile connections
```

### Step 3.3: Install dbt Dependencies

```bash
# Install packages from packages.yml
uv run dbt deps

# Should download any required dbt packages
```

### Step 3.4: Run dbt Models (Dev Target - DuckDB)

```bash
# First, run against DuckDB for local testing
uv run dbt run --target dev

# Expected output: All models created successfully
# Check that staging and marts models were created
```

### Step 3.5: Run dbt Models (Prod Target - PostgreSQL)

```bash
# Make sure PostgreSQL is running and has raw data
# Then run models against PostgreSQL
uv run dbt run --target prod

# Expected output: Staging and mart models created in PostgreSQL
```

### Step 3.6: Test dbt Models

```bash
# Run dbt tests (if tests defined in .yml files)
uv run dbt test

# Generate documentation
uv run dbt docs generate

# Serve documentation (optional)
# uv run dbt docs serve --port 8001
```

**Phase 3 Checkpoint:** ✅ dbt models run, transformations applied, data marts created

---

## 📊 Phase 4: Analytics & Dashboards

### Step 4.1: Update Streamlit Views

```bash
# Update Streamlit pages to query dbt marts instead of raw data
# Files to update:
# - app/views/04_Indicators.py (query technical indicators from dbt)
# - app/views/05_Analysis.py (create analytics dashboards)

# Run Streamlit with PostgreSQL connection
export POSTGRES_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/stocks"
uv run streamlit run app/main.py
```

### Step 4.2: Test Analytics Queries

```bash
# Run sample SQL queries against dbt marts
docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c "
SELECT * FROM fct_daily_prices LIMIT 5;
"

docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c "
SELECT * FROM fct_technical_indicators LIMIT 5;
"
```

**Phase 4 Checkpoint:** ✅ Analytics dashboards display dbt-generated insights

---

## 🤖 Phase 5: LLM + RAG Integration (Optional)

### Step 5.1: Install Phase 5 Dependencies

```bash
# Add Phase 5 (LLM/RAG) dependencies
uv sync --extra phase1 --extra phase2 --extra phase3 --extra phase5

# Or all at once
uv sync --extra all
```

### Step 5.2: Start Ollama Service

```bash
# Start Ollama with Docker Compose
docker-compose up -d ollama

# Wait for Ollama to be ready
sleep 5

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### Step 5.3: Pull LLM Models

```bash
# Initialize Ollama and pull a model
bash scripts/init_ollama.sh

# Or manually pull models
curl -X POST http://localhost:11434/api/pull -d '{"name":"mistral"}'

# List available models
curl http://localhost:11434/api/tags
```

**Expected:** Mistral model (or chosen model) should be listed.

### Step 5.4: Test LLM Connection

```bash
# Test Ollama API endpoint
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"mistral","prompt":"What is the capital of France?","stream":false}'
```

**Expected:** LLM response should appear.

### Step 5.5: Run RAG Chat Interface

```bash
# Make sure all services are running
docker-compose up

# In another terminal, run Streamlit (Phase 5)
uv run streamlit run app/main.py

# Navigate to "06_AI_Analyst" page
# Chat with the LLM using RAG on your data
```

**Phase 5 Checkpoint:** ✅ LLM responds, RAG integrates with financial data, chat works

---

## 🧪 Complete Integration Test

### Full End-to-End Test (All Services Running)

```bash
# Terminal 1: Start all Docker services
docker-compose up

# Wait for services to be ready (30-60 seconds)
sleep 30

# Terminal 2: Check service health
docker-compose ps

# Expected: All services showing "Up" status

# Terminal 3: Run Streamlit
export POSTGRES_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/stocks"
export AIRFLOW_HOME=$(pwd)/airflow
uv run streamlit run app/main.py

# Terminal 4: Start Airflow services (if using Airflow)
export AIRFLOW_HOME=$(pwd)/airflow
uv run airflow scheduler &
uv run airflow webserver --port 8080

# Terminal 5: Trigger Airflow DAG
export AIRFLOW_HOME=$(pwd)/airflow
uv run airflow dags trigger etl_prices_dag

# Terminal 6: Monitor data flow
watch -n 5 "docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c 'SELECT COUNT(*) FROM prices;'"
```

### Verification Checklist

```
✅ Docker services running (postgres, ollama, streamlit)
✅ Streamlit app loads at http://localhost:8501
✅ Airflow UI accessible at http://localhost:8080
✅ Data in PostgreSQL (prices table populated)
✅ dbt models created (staging and marts)
✅ Ollama responding at http://localhost:11434
✅ All Streamlit pages load
✅ Chat/RAG interface works (Phase 5)
```

---

## 🛑 Stopping & Cleaning Up

### Stop All Services

```bash
# Stop all Docker containers
docker-compose down

# Stop Airflow services (if running locally)
# Ctrl+C on scheduler and webserver terminals

# Optionally, remove volumes
docker-compose down -v
```

### Clean Project Cache

```bash
# Remove Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove dbt artifacts
rm -rf dbt/target/
rm -rf dbt/logs/
rm -rf dbt_packages/

# Remove Airflow DB (to reset)
rm airflow/airflow.db
```

### Remove Local Database

```bash
# Remove DuckDB
rm data/app.duckdb

# Clear PostgreSQL (via Docker)
docker exec -it de-bootcamp-postgres psql -U postgres -c "DROP DATABASE stocks;"
```

---

## 🔧 Troubleshooting Common Issues

### Issue: DuckDB Permission Denied

**Solution:**
```bash
chmod 644 data/app.duckdb
```

### Issue: PostgreSQL Connection Refused

**Solution:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# If not running, start it
docker-compose up -d postgres

# Check logs
docker-compose logs postgres
```

### Issue: Airflow DAG Not Appearing

**Solution:**
```bash
# Check AIRFLOW_HOME is set correctly
echo $AIRFLOW_HOME

# Check DAG file syntax
uv run python -m py_compile airflow/dags/etl_prices_dag.py

# Restart Airflow scheduler
# Ctrl+C on scheduler, then restart
uv run airflow scheduler
```

### Issue: dbt Model Compilation Failed

**Solution:**
```bash
# Check dbt profiles
uv run dbt debug

# Parse and check YAML files
uv run dbt parse

# Clear dbt artifacts and retry
rm -rf dbt/target/ && uv run dbt run
```

### Issue: Ollama Model Not Found

**Solution:**
```bash
# Pull the model manually
curl -X POST http://localhost:11434/api/pull -d '{"name":"mistral"}'

# Wait for download to complete
# Check available models
curl http://localhost:11434/api/tags
```

### Issue: Streamlit Page Errors

**Solution:**
```bash
# Clear Streamlit cache
rm -rf ~/.streamlit/

# Run with debug mode
uv run streamlit run app/main.py --logger.level=debug
```

---

## 📋 Quick Command Reference

| Phase | Command | Purpose |
|-------|---------|---------|
| 0 | `uv sync --extra phase1` | Install Phase 1 dependencies |
| 0 | `cp .env.example .env` | Setup environment |
| 1 | `uv run streamlit run app/main.py` | Run Streamlit locally |
| 1 | `uv run python -m scripts.refresh_data` | Run ETL manually |
| 2 | `docker-compose up -d postgres` | Start PostgreSQL |
| 2 | `uv run airflow scheduler` | Start Airflow scheduler |
| 2 | `uv run airflow webserver --port 8080` | Start Airflow UI |
| 3 | `uv run dbt run --target prod` | Run dbt models |
| 3 | `uv run dbt test` | Test dbt models |
| 4 | `curl http://localhost:5432` | Test PostgreSQL connection |
| 5 | `docker-compose up -d ollama` | Start Ollama |
| 5 | `curl http://localhost:11434/api/tags` | Check LLM models |

---

## ✅ Completion Checklist

- [ ] Phase 0: Repository created, Python environment ready
- [ ] Phase 1: Streamlit running, yfinance data loads
- [ ] Phase 2: PostgreSQL populated, Airflow DAGs execute
- [ ] Phase 3: dbt models compile, transformations apply
- [ ] Phase 4: Analytics dashboards display data
- [ ] Phase 5: Ollama responds, RAG chat works

---

## 📞 Getting Help

- Check `README.md` for project overview
- Read phase-specific docs in `docs/` folder
- Review code comments in Python files
- Check Docker logs: `docker-compose logs <service>`
- Test component individually before integration

---

**Last Updated:** May 2026  
**Total Setup Time:** 1-2 hours (all phases)  
**Learning Time:** 8-15 hours (2-3 hours per phase)
