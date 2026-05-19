# Phase 2: Apache Airflow + PostgreSQL

## Overview

Phase 2 teaches you how to:
- Automate data pipelines with Apache Airflow
- Store historical data in PostgreSQL (persistent data warehouse)
- Schedule daily ETL jobs
- Monitor pipeline execution
- Handle failures and retries

**Time to Complete:** 2-3 hours  
**Tech Stack:** Apache Airflow, PostgreSQL, Docker, Docker Compose

**Prerequisites:** Complete Phase 1 (Streamlit + yfinance working)

---

## Learning Goals

- ✅ Understand DAGs (Directed Acyclic Graphs) and task dependencies
- ✅ Write Airflow DAGs for ETL pipelines
- ✅ Set up PostgreSQL as data warehouse
- ✅ Schedule recurring jobs (daily, hourly, etc.)
- ✅ Monitor jobs in Airflow UI
- ✅ Handle errors, retries, and notifications
- ✅ Use Docker Compose to run services

---

## Architecture

```
yfinance API
    ↓
Airflow DAG (etl_prices_dag)
    ↓
Task 1: Download prices from yfinance
Task 2: Validate data quality
Task 3: Load into PostgreSQL
    ↓
PostgreSQL Database
    ↓
Streamlit App (Phase 1 now uses PostgreSQL instead of DuckDB)
```

---

## Getting Started

### Step 1: Start PostgreSQL with Docker

```bash
# Start PostgreSQL in background
docker-compose up -d postgres

# Wait for it to be ready (should show "Up" status)
docker-compose ps postgres

# Test connection
docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c "SELECT version();"
```

**Expected:** PostgreSQL 15 version information displayed.

### Step 2: Initialize Database Schema

Create tables in PostgreSQL:

```bash
# Run initialization script (TODO: implement in scripts/init_db.py)
uv run python scripts/init_db.py
```

**Tables to Create:**
```sql
CREATE TABLE prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open FLOAT NOT NULL,
    high FLOAT NOT NULL,
    low FLOAT NOT NULL,
    close FLOAT NOT NULL,
    volume BIGINT NOT NULL,
    UNIQUE(symbol, timestamp)
);

CREATE TABLE watchlist (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prices_symbol_timestamp ON prices(symbol, timestamp);
```

### Step 3: Install Phase 2 Dependencies

```bash
# Install Airflow packages
uv sync --extra phase1 --extra phase2

# Verify Airflow installation
uv run airflow version
```

### Step 4: Initialize Airflow

```bash
# Set environment variables
export AIRFLOW_HOME=$(pwd)/airflow
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/airflow/dags
export AIRFLOW__CORE__LOAD_EXAMPLES=False

# Initialize Airflow database
uv run airflow db init

# Create admin user (interactive prompt)
uv run airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```

### Step 5: Start Airflow Services

**Terminal 1: Airflow Scheduler**
```bash
export AIRFLOW_HOME=$(pwd)/airflow
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/airflow/dags
export AIRFLOW__CORE__LOAD_EXAMPLES=False

uv run airflow scheduler
```

**Terminal 2: Airflow Webserver**
```bash
export AIRFLOW_HOME=$(pwd)/airflow
uv run airflow webserver --port 8080
```

**Terminal 3: Verify DAGs**
```bash
export AIRFLOW_HOME=$(pwd)/airflow
uv run airflow dags list

# Should show:
# etl_prices_dag
# example_placeholder_dag
```

### Step 6: Access Airflow UI

Open browser to: **http://localhost:8080**  
Login: `admin` / `admin`

---

## Key Concepts

### 1. Apache Airflow

**What is Airflow?**  
Workflow orchestration platform. Define data pipelines as code (DAGs), schedule them, and monitor execution.

**Why Airflow?**
- Schedule workflows at specific times or intervals
- Handle task dependencies
- Retry failed tasks automatically
- Monitor job status and logs
- Handle complex data pipelines
- Industry standard (used at Netflix, Uber, Airbnb)

### 2. DAGs (Directed Acyclic Graphs)

**Concept:**
- **DAG:** Collection of tasks with dependencies
- **Task:** Unit of work (e.g., download data, validate, insert)
- **Operator:** Type of task (Python, Bash, SQL, etc.)

**Example DAG Structure:**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Define default arguments
default_args = {
    'owner': 'data-eng',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
with DAG(
    'my_pipeline',
    default_args=default_args,
    schedule_interval='0 9 * * *',  # 9 AM daily
    start_date=datetime(2026, 5, 1),
    catchup=False,
) as dag:
    # Define tasks
    task1 = PythonOperator(task_id='extract', python_callable=extract_data)
    task2 = PythonOperator(task_id='transform', python_callable=transform_data)
    task3 = PythonOperator(task_id='load', python_callable=load_data)
    
    # Set dependencies: task1 → task2 → task3
    task1 >> task2 >> task3
```

### 3. PostgreSQL

**What is PostgreSQL?**  
Production-grade relational database. Replaces DuckDB for Phase 2+.

**Connection from Python:**
```python
from sqlalchemy import create_engine

postgres_url = "postgresql+psycopg2://postgres:postgres@localhost:5432/stocks"
engine = create_engine(postgres_url)

# Insert data
with engine.connect() as conn:
    conn.execute("INSERT INTO prices VALUES (...)")
    conn.commit()

# Query data
with engine.connect() as conn:
    result = conn.execute("SELECT * FROM prices")
```

### 4. Docker & Docker Compose

**What is Docker Compose?**  
Runs multiple services (PostgreSQL, Ollama, Streamlit) with one command.

**Key Service Configuration:**
```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: stocks
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

**Commands:**
```bash
docker-compose up -d postgres      # Start PostgreSQL
docker-compose ps                   # Show running services
docker-compose logs postgres        # View logs
docker-compose down                 # Stop all services
```

---

## TODO: Implement Phase 2 Tasks

### ETL DAG (airflow/dags/etl_prices_dag.py)

Implement a DAG with these tasks:

1. **Task 1: Download Data**
   - [ ] Use yfinance to download prices for all symbols in config
   - [ ] Store result in task context (XCom) for next task
   - [ ] Handle download errors

2. **Task 2: Validate Data**
   - [ ] Check data quality: no NULL values in OHLCV columns
   - [ ] Validate price logic: low ≤ open ≤ high ≤ close (not always true, but check extremes)
   - [ ] Check timestamp is recent
   - [ ] Skip insert if validation fails

3. **Task 3: Load to PostgreSQL**
   - [ ] Connect to PostgreSQL
   - [ ] Insert prices into `prices` table
   - [ ] Handle duplicate timestamp+symbol (upsert or skip)
   - [ ] Log rows inserted

4. **Task 4: Notify** (optional)
   - [ ] Log success message
   - [ ] Send notification if failed

**Schedule:** Daily at 8:00 AM (or adjust as needed)

---

## Airflow UI Guide

### Dashboard
- Overall status of DAGs and recent task runs
- Success/failure rates
- Execution timeline

### DAGs View
- List of all DAGs
- Enable/disable DAGs
- View DAG code
- Trigger DAG manually

### Graph View
- Visualize task dependencies
- Click task to see logs
- View task status (success, failed, running)

### Tree View
- Historical view of all DAG runs
- Status of each task execution
- Drill down to task logs

### Logs
- View task execution logs
- Debugging failed tasks
- Performance metrics

---

## Common Airflow Operators

```python
# Python function
from airflow.operators.python import PythonOperator

def my_task():
    print("Hello from Airflow!")

task = PythonOperator(task_id='my_task', python_callable=my_task, dag=dag)

# SQL execution
from airflow.operators.postgres_operator import PostgresOperator

task = PostgresOperator(
    task_id='run_query',
    sql='INSERT INTO prices VALUES (...)',
    postgres_conn_id='postgres_default',
    dag=dag,
)

# Bash command
from airflow.operators.bash import BashOperator

task = BashOperator(
    task_id='bash_task',
    bash_command='echo "Hello from Bash"',
    dag=dag,
)
```

---

## Setting up PostgreSQL Connection in Airflow

1. Go to Airflow UI → Admin → Connections
2. Click "Create"
3. Fill in:
   - Conn Id: `postgres_default`
   - Conn Type: `Postgres`
   - Host: `postgres` (or `localhost` if local)
   - Login: `postgres`
   - Password: `postgres`
   - Port: `5432`
   - Database: `stocks`
4. Click "Save"

---

## Troubleshooting

### Issue: "Connection refused" to PostgreSQL
**Solution:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# If not running, start it
docker-compose up -d postgres

# Wait 10 seconds for startup
sleep 10
```

### Issue: Airflow can't find DAG file
**Solution:**
```bash
# Check AIRFLOW_HOME and AIRFLOW__CORE__DAGS_FOLDER are set
echo $AIRFLOW_HOME
echo $AIRFLOW__CORE__DAGS_FOLDER

# Verify DAG file syntax
uv run python -m py_compile airflow/dags/etl_prices_dag.py
```

### Issue: Task fails with "psycopg2.OperationalError"
**Solution:**
```bash
# Verify PostgreSQL is accessible
docker exec -it de-bootcamp-postgres psql -U postgres -d stocks -c "SELECT 1"

# Check connection string in .env
echo $POSTGRES_URL
```

### Issue: DAG not triggering automatically
**Solution:**
```bash
# Ensure scheduler is running (see Terminal 1 output)
# Check DAG pause status in Airflow UI (should not be paused)
# Verify schedule_interval is set correctly (not None)
# Check `catchup=False` in DAG definition
```

---

## Next Steps After Phase 2

Once you're comfortable with:
- Writing Airflow DAGs
- Scheduling recurring jobs
- PostgreSQL for data storage
- Monitoring pipeline execution

You're ready for **Phase 3: dbt Data Transformations**!

See [PHASE_3_DBT.md](PHASE_3_DBT.md)
