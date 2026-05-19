-- Mart: fct_daily_prices
-- Daily price aggregations and metrics

-- TODO: Implement daily fact table:
-- 1. Aggregate 5-min data to daily
-- 2. Calculate daily metrics (high, low, volume, etc.)
-- 3. Add performance indicators

SELECT
    symbol,
    DATE(timestamp) AS date,
    MIN(open) AS daily_open,
    MAX(high) AS daily_high,
    MIN(low) AS daily_low,
    MAX(close) AS daily_close,
    SUM(volume) AS daily_volume
FROM {{ ref('stg_prices') }}
GROUP BY symbol, DATE(timestamp)
ORDER BY symbol, date
