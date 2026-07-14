{{ config(materialized='view') }}

select
    id,
    symbol,
    ingestion_type,
    status,
    rows_ingested,
    started_at,
    completed_at
from {{ source('raw', 'ingestion_log') }}
