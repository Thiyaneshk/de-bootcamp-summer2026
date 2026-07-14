{{ config(materialized='view') }}

select
    symbol,
    name,
    instrument_type,
    exchange,
    is_active,
    created_at,
    updated_at
from {{ source('raw', 'instruments') }}
