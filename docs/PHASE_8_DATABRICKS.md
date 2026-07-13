# Phase 8: Databricks Lakehouse

## Overview

In this phase, we add Databricks as a parallel processing layer. While Snowflake handles SQL analytics, Databricks provides a Spark-based environment for large-scale historical data processing, ML feature engineering, and the Medallion architecture (Bronze -> Silver -> Gold).

**Time to Complete:** 1.5 hours
**Tech Stack:** Databricks, PySpark, Delta Lake, Airflow (`apache-airflow-providers-databricks`)

---

## What We Built

1. **Databricks Notebooks:** Created PySpark scripts in `databricks/notebooks/` to ingest raw data (Bronze), clean it (Silver), and compute features (Gold).
2. **Databricks Jobs:** Defined a multi-task job configuration in `databricks/jobs/daily_ingest_job.json`.
3. **Airflow DAG:** Created `airflow/dags/databricks_ingest_dag.py` to trigger the Databricks job from our orchestration layer.
4. **Terraform Scaffold:** Initialized a Databricks module at `terraform/modules/databricks/` to manage the Spark cluster as code.

---

## Core Concepts

### Lakehouse Architecture
A data lakehouse combines the flexibility of data lakes (object storage, unstructured data) with the management and ACID transactions of data warehouses. Databricks builds this using Delta Lake.

### Medallion Architecture
A recommended data design pattern:
- **Bronze:** Raw, untransformed data as ingested from sources.
- **Silver:** Cleaned, deduplicated, and validated data.
- **Gold:** Aggregated data, feature engineered data ready for ML models and BI.

### PySpark & Delta Lake
Instead of standard Pandas DataFrames which process in-memory on a single machine, PySpark distributes the computation across a cluster. Delta Lake stores this data with ACID transaction guarantees.

---

## Validation / Acceptance Criteria

1. **Cluster Setup:** Configure Databricks credentials in `.env` and create the cluster (or apply via Terraform).
2. **Run Notebooks:** Manually execute `01_ingest_yfinance.py` to ensure it writes a Bronze table to Delta format.
3. **Trigger via Airflow:** Check the Airflow UI, enable `databricks_daily_ingest`, and trigger a run to verify integration.
4. **Data Verification:** Use Spark SQL or Databricks SQL to confirm tables `bootcamp.bronze.raw_prices`, `bootcamp.silver.prices_clean`, and `bootcamp.gold.features` have data.

---

## Next Steps

Now that we have all the components, it's time to provision and manage everything using Infrastructure as Code.

Proceed to [Phase 9: HashiCorp Terraform IaaS](PHASE_9_TERRAFORM.md).
