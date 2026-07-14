"""
Phase 2: Example Placeholder DAG

Simple placeholder DAG for testing Airflow setup.
"""

from datetime import datetime

from airflow.operators.bash import BashOperator

from airflow import DAG

dag = DAG(
    "example_placeholder_dag",
    description="Placeholder DAG for testing",
    schedule_interval=None,
    start_date=datetime(2026, 5, 1),
    catchup=False,
)

hello_task = BashOperator(
    task_id="hello_task",
    bash_command="echo 'DAG is working!'",
    dag=dag,
)
