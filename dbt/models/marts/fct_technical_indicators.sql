-- Mart: fct_technical_indicators
-- Technical indicators (RSI, MACD, SMA, etc.)

-- TODO: Implement technical indicators:
-- 1. Simple Moving Average (SMA) - 20, 50, 200 day
-- 2. Relative Strength Index (RSI) - 14 day
-- 3. MACD (Moving Average Convergence Divergence)
-- 4. Bollinger Bands
-- 5. Volume indicators

SELECT
    symbol,
    timestamp,
    close,
    AVG(close) OVER (PARTITION BY symbol ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS sma_20,
    AVG(close) OVER (PARTITION BY symbol ORDER BY timestamp ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS sma_50
FROM {{ ref('stg_prices') }}
ORDER BY symbol, timestamp
