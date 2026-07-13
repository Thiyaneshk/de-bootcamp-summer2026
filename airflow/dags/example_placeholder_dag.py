"""
Phase 2: Example Placeholder DAG

Simple placeholder DAG for testing Airflow setup.

TODO: Replace with actual ETL logic or remove after testing.
"""

from datetime import datetime

from airflow import DAG

dag = DAG(
    "example_placeholder_dag",
    description="Placeholder DAG for testing",
    schedule_interval=None,
    start_date=datetime(2026, 5, 1),
    catchup=False,
)


# TODO: Define placeholder tasks
# task1 = BashOperator(task_id='echo_hello', bash_command='echo "Hello from Airflow"', dag=dag)
