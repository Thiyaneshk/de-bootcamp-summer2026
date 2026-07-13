"""Snowflake connection — production data warehouse for Phase 7+."""
import os

import pandas as pd
import snowflake.connector


def get_snowflake_connection():
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "BOOTCAMP_DB"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
    )

def query_snowflake(sql: str) -> pd.DataFrame:
    conn = get_snowflake_connection()
    with conn.cursor() as cur:
        cur.execute(sql)
        df = cur.fetch_pandas_all()
    conn.close()
    return df
