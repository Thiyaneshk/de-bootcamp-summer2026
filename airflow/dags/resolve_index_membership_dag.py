"""Weekly DAG for resolving index memberships into the registry."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from app.db.registry import add_instrument, upsert_index_constituents


def resolve_index_membership(**context):
    add_instrument("^GSPC", name="S&P 500", instrument_type="index", exchange="INDEX")
    upsert_index_constituents("^GSPC", [{"stock_symbol": "AAPL", "weight": 0.06}, {"stock_symbol": "MSFT", "weight": 0.05}])
    return {"status": "ok"}


with DAG(
    dag_id="resolve_index_membership",
    default_args={
        "owner": "data-eng",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        "start_date": datetime(2026, 5, 1),
    },
    schedule_interval="0 0 * * 0",
    catchup=False,
    tags=["registry", "index", "membership"],
) as dag:
    PythonOperator(task_id="resolve_index_membership", python_callable=resolve_index_membership)
