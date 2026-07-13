# Phase 7: Snowflake Cloud Data Warehouse

## Overview

In this phase, we transition from local PostgreSQL to **Snowflake**, a fully managed cloud data warehouse. We will keep PostgreSQL for local development fallback, but use Snowflake for our production pipeline.

**Time to Complete:** 1.5 hours
**Tech Stack:** Snowflake, Python (`snowflake-connector-python`), dbt (`dbt-snowflake`)

---

## What We Built

1. **Terraform Scaffold:** Created a `terraform/modules/snowflake/` directory to define our warehouse, database, and schemas using HashiCorp Terraform (Infrastructure as Code).
2. **Connector:** Implemented `app/db/snowflake_connector.py` for Python interactions with Snowflake.
3. **Database Router:** Updated `app/db/__init__.py` to support `DB_BACKEND="snowflake"`.
4. **dbt Configuration:** Added a `snowflake` target in `dbt/profiles.yml`.
5. **Dependencies:** Added `snowflake-connector-python` and `dbt-snowflake`.

---

## Core Concepts

### Cloud Data Warehouse
Snowflake separates storage (databases, schemas, tables) from compute (virtual warehouses). This allows you to scale compute independently based on workload (e.g. use an XL warehouse for heavy dbt runs, and an XS warehouse for Streamlit queries).

### Role-Based Access Control (RBAC)
Snowflake uses roles to manage access. For this bootcamp, we configure the `ACCOUNTADMIN` role, but in production, you would create custom roles for `dbt_runner` and `streamlit_reader`.

### dbt with Snowflake
Unlike PostgreSQL which runs on your machine, `dbt run --target snowflake` compiles your SQL locally but pushes the computation to Snowflake servers.

---

## Validation / Acceptance Criteria

1. **Credentials:** Set up a free Snowflake trial and populate `.env` variables (`SNOWFLAKE_ACCOUNT`, etc.).
2. **Setup DB:** (Requires Phase 9 to fully provision, but you can manually create the database/schema in the Snowflake UI).
3. **Run dbt:**
   ```bash
   uv run dbt run --profiles-dir dbt --target snowflake
   ```
4. **Run App:**
   Start your Streamlit app with `DB_BACKEND=snowflake`. It should display data directly from the cloud.

---

## Next Steps

With our data warehouse in the cloud, we can move our heavy batch processing to a Lakehouse.

Proceed to [Phase 8: Databricks Lakehouse](PHASE_8_DATABRICKS.md).
