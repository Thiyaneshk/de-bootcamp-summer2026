"""Phase 8: Trigger Databricks notebook via Airflow."""
from datetime import datetime, timedelta

from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator

from airflow import DAG

with DAG(
    dag_id="databricks_daily_ingest",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
) as dag:

    ingest = DatabricksRunNowOperator(
        task_id="run_bronze_ingestion",
        databricks_conn_id="databricks_default",
        job_id="{{ var.value.databricks_ingest_job_id }}",
    )
