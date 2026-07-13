"""Database connection and utilities"""

import os

# Add Snowflake as a third option alongside DuckDB and PostgreSQL
DB_BACKEND = os.getenv("DB_BACKEND", "duckdb")  # "duckdb" | "postgres" | "snowflake"
