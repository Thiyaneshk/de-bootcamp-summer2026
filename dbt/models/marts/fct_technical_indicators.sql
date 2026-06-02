-- Mart: fct_technical_indicators
-- Technical indicators (EMA50, EMA200, SMA20, SMA50)

WITH RECURSIVE ordered_prices AS (
    SELECT
        symbol,
        timestamp,
        close,
        -- Simple Moving Averages (built-in window function)
        AVG(close) OVER (PARTITION BY symbol ORDER BY timestamp ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS sma_20,
        AVG(close) OVER (PARTITION BY symbol ORDER BY timestamp ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS sma_50,
        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY timestamp) AS rn
    FROM {{ ref('stg_prices') }}
),

ema_calc AS (
    -- Base Case: First trading day initialized to the close price
    SELECT
        symbol,
        timestamp,
        close,
        rn,
        sma_20,
        sma_50,
        close AS ema_50,
        close AS ema_200
    FROM ordered_prices
    WHERE rn = 1

    UNION ALL

    -- Recursive Step: Exponential Moving Average formula
    -- alpha = 2 / (period + 1)
    -- alpha_50 = 2 / 51 = 0.03921568627
    -- alpha_200 = 2 / 201 = 0.009950248756
    SELECT
        p.symbol,
        p.timestamp,
        p.close,
        p.rn,
        p.sma_20,
        p.sma_50,
        ((p.close * 0.03921568627) + (e.ema_50 * (1.0 - 0.03921568627))) AS ema_50,
        ((p.close * 0.009950248756) + (e.ema_200 * (1.0 - 0.009950248756))) AS ema_200
    FROM ordered_prices p
    JOIN ema_calc e ON p.symbol = e.symbol AND p.rn = e.rn + 1
)

SELECT
    symbol,
    timestamp,
    close,
    ROUND(sma_20::numeric, 4) AS sma_20,
    ROUND(sma_50::numeric, 4) AS sma_50,
    ROUND(ema_50::numeric, 4) AS ema_50,
    ROUND(ema_200::numeric, 4) AS ema_200
FROM ema_calc
ORDER BY symbol, timestamp
