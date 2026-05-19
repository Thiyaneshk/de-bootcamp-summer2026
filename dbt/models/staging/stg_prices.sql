-- Staging: stg_prices
-- Clean and standardize raw price data

-- TODO: Implement staging transformations:
-- 1. Remove duplicates
-- 2. Handle NULL values
-- 3. Validate data types
-- 4. Add calculated fields (pct_change, etc.)

SELECT
    symbol,
    timestamp,
    open,
    high,
    low,
    close,
    volume,
    ROUND(((close - LAG(close) OVER (PARTITION BY symbol ORDER BY timestamp)) / LAG(close) OVER (PARTITION BY symbol ORDER BY timestamp)) * 100, 2) AS pct_change
FROM {{ source('raw', 'prices') }}
WHERE symbol IS NOT NULL
    AND timestamp IS NOT NULL
    AND close > 0
ORDER BY symbol, timestamp
