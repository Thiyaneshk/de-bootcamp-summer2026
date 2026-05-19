"""
Phase 2: ETL Prices DAG

Apache Airflow DAG for scheduled yfinance data ingestion to PostgreSQL.

TODO: Implement DAG:
- Task 1: Download prices from yfinance
- Task 2: Validate data quality
- Task 3: Insert into PostgreSQL
- Task 4: Log completion
- Schedule: Daily at 8 AM
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta


default_args = {
    'owner': 'data-eng',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 5, 1),
}


dag = DAG(
    'etl_prices_dag',
    default_args=default_args,
    description='Daily ETL pipeline for yfinance data',
    schedule_interval='0 8 * * *',  # 8 AM daily
    catchup=False,
)


# TODO: Define tasks
# download_task = PythonOperator(task_id='download_prices', ...)
# validate_task = PythonOperator(task_id='validate_data', ...)
# insert_task = PythonOperator(task_id='insert_postgres', ...)

# TODO: Set task dependencies
# download_task >> validate_task >> insert_task
