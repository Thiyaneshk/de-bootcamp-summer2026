-- One-time PostgreSQL initialization
-- Creates both databases on the single Postgres instance
-- This script runs automatically when the postgres container first starts

-- Database for stock price data (used by Streamlit + Airflow DAG + dbt)
SELECT 'CREATE DATABASE stocks'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'stocks')\gexec

-- Database for Airflow metadata (task states, DAG history, logs)
SELECT 'CREATE DATABASE airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec

-- Connect to stocks DB and create the prices table schema
\connect stocks

CREATE TABLE IF NOT EXISTS prices (
    symbol    VARCHAR(20)  NOT NULL,
    timestamp TIMESTAMPTZ  NOT NULL,
    open      DOUBLE PRECISION,
    high      DOUBLE PRECISION,
    low       DOUBLE PRECISION,
    close     DOUBLE PRECISION,
    volume    BIGINT,
    PRIMARY KEY (symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_prices_symbol ON prices (symbol);
CREATE INDEX IF NOT EXISTS idx_prices_timestamp ON prices (timestamp DESC);

COMMENT ON TABLE prices IS 'Daily OHLCV stock prices loaded by Airflow ETL';
