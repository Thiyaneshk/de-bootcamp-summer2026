"""
Phase 2: ETL Prices DAG

Apache Airflow DAG for scheduled yfinance data ingestion to PostgreSQL.

Implements daily refresh of stock prices:
- Loads symbols from config/symbols.toml
- Downloads daily OHLCV data via yfinance
- Upserts into PostgreSQL prices table
- Logs completion

Schedule: Daily at 8 AM UTC
"""

import logging
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


def refresh_all_symbols(**context):
    """Refresh all configured symbols using the ETL script."""
    from scripts.refresh_data import refresh_all
    
    logger.info("Starting ETL refresh for all configured symbols")
    refresh_all()
    logger.info("ETL refresh completed")


def refresh_specific_symbols(symbols: list[str], **context):
    """Refresh specific symbols."""
    from scripts.refresh_data import refresh_symbols
    
    logger.info(f"Refreshing symbols: {symbols}")
    refresh_symbols(symbols)
    logger.info(f"Completed refresh for {len(symbols)} symbols")


def validate_data_loaded(**context):
    """Validate that data was loaded into PostgreSQL."""
    from sqlalchemy import create_engine, text
    
    postgres_url = os.getenv('POSTGRES_URL')
    if not postgres_url:
        logger.warning("POSTGRES_URL not set, skipping validation")
        return
    
    engine = create_engine(postgres_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM prices"))
        row_count = result.fetchone()[0]
        logger.info(f"✓ Data validation: {row_count} total rows in prices table")
        
        # Get symbol count
        result = conn.execute(text("SELECT COUNT(DISTINCT symbol) FROM prices"))
        symbol_count = result.fetchone()[0]
        logger.info(f"✓ Symbols loaded: {symbol_count} unique symbols")
        
        return {'total_rows': row_count, 'symbols': symbol_count}


default_args = {
    'owner': 'data-eng',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 5, 1),
    'email_on_failure': False,
}


dag = DAG(
    'etl_prices_dag',
    default_args=default_args,
    description='Daily ETL pipeline for yfinance data to PostgreSQL',
    schedule_interval='0 8 * * *',  # 8 AM UTC daily
    catchup=False,
    tags=['price-data', 'yfinance', 'postgres'],
)


# Task 1: Refresh all configured symbols
refresh_task = PythonOperator(
    task_id='refresh_prices',
    python_callable=refresh_all_symbols,
    dag=dag,
)

# Task 2: Validate data loaded
validate_task = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data_loaded,
    dag=dag,
)

# Set dependencies
refresh_task >> validate_task

