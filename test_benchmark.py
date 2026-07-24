import time

import numpy as np
import pandas as pd

# Create dummy data
np.random.seed(42)
n = 100000
df = pd.DataFrame(
    {
        "timestamp": pd.date_range("2020-01-01", periods=n, freq="D"),
        "close": np.random.randn(n).cumsum() + 100,
        "sma_20": np.random.randn(n).cumsum() + 100,
        "sma_50": np.random.randn(n).cumsum() + 100,
        "ema_50": np.random.randn(n).cumsum() + 100,
        "ema_200": np.random.randn(n).cumsum() + 100,
    }
)


def detect_crossovers_original(df: pd.DataFrame) -> list[dict]:
    events = []
    if len(df) < 2:
        return events

    # SMA 20 vs SMA 50
    df = df.copy()
    df["sma_diff"] = df["sma_20"] - df["sma_50"]
    df["sma_diff_prev"] = df["sma_diff"].shift(1)

    # EMA 50 vs EMA 200
    df["ema_diff"] = df["ema_50"] - df["ema_200"]
    df["ema_diff_prev"] = df["ema_diff"].shift(1)

    for i in range(1, len(df)):
        row = df.iloc[i]
        date_str = row["timestamp"].strftime("%Y-%m-%d")

        # SMA Golden / Death Cross
        if pd.notna(row["sma_diff"]) and pd.notna(row["sma_diff_prev"]):
            if row["sma_diff"] > 0 >= row["sma_diff_prev"]:
                events.append(
                    {
                        "date": date_str,
                        "timestamp": row["timestamp"],
                        "type": "Golden Cross (SMA 20/50)",
                        "desc": f"SMA 20 crossed above SMA 50 at {row['close']:.2f}",
                        "is_bullish": True,
                    }
                )
            elif row["sma_diff"] < 0 <= row["sma_diff_prev"]:
                events.append(
                    {
                        "date": date_str,
                        "timestamp": row["timestamp"],
                        "type": "Death Cross (SMA 20/50)",
                        "desc": f"SMA 20 crossed below SMA 50 at {row['close']:.2f}",
                        "is_bullish": False,
                    }
                )

        # EMA Golden / Death Cross
        if pd.notna(row["ema_diff"]) and pd.notna(row["ema_diff_prev"]):
            if row["ema_diff"] > 0 >= row["ema_diff_prev"]:
                events.append(
                    {
                        "date": date_str,
                        "timestamp": row["timestamp"],
                        "type": "Golden Cross (EMA 50/200)",
                        "desc": f"EMA 50 crossed above EMA 200 at {row['close']:.2f}",
                        "is_bullish": True,
                    }
                )
            elif row["ema_diff"] < 0 <= row["ema_diff_prev"]:
                events.append(
                    {
                        "date": date_str,
                        "timestamp": row["timestamp"],
                        "type": "Death Cross (EMA 50/200)",
                        "desc": f"EMA 50 crossed below EMA 200 at {row['close']:.2f}",
                        "is_bullish": False,
                    }
                )

    return sorted(events, key=lambda x: x["timestamp"], reverse=True)


start_time = time.time()
res1 = detect_crossovers_original(df)
end_time = time.time()
print(f"Original logic: {end_time - start_time:.4f} seconds")


def detect_crossovers_optimized(df: pd.DataFrame) -> list[dict]:
    events = []
    if len(df) < 2:
        return events

    # We need a copy to avoid SettingWithCopyWarning if it's a slice
    df = df.copy()

    # SMA 20 vs SMA 50
    df["sma_diff"] = df["sma_20"] - df["sma_50"]
    df["sma_diff_prev"] = df["sma_diff"].shift(1)

    # EMA 50 vs EMA 200
    df["ema_diff"] = df["ema_50"] - df["ema_200"]
    df["ema_diff_prev"] = df["ema_diff"].shift(1)

    # Boolean indexing for SMA Golden Cross
    sma_golden_mask = (
        (df["sma_diff"] > 0)
        & (df["sma_diff_prev"] <= 0)
        & df["sma_diff"].notna()
        & df["sma_diff_prev"].notna()
    )

    # Boolean indexing for SMA Death Cross
    sma_death_mask = (
        (df["sma_diff"] < 0)
        & (df["sma_diff_prev"] >= 0)
        & df["sma_diff"].notna()
        & df["sma_diff_prev"].notna()
    )

    # Boolean indexing for EMA Golden Cross
    ema_golden_mask = (
        (df["ema_diff"] > 0)
        & (df["ema_diff_prev"] <= 0)
        & df["ema_diff"].notna()
        & df["ema_diff_prev"].notna()
    )

    # Boolean indexing for EMA Death Cross
    ema_death_mask = (
        (df["ema_diff"] < 0)
        & (df["ema_diff_prev"] >= 0)
        & df["ema_diff"].notna()
        & df["ema_diff_prev"].notna()
    )

    # Create event records from vectorized boolean masks
    for idx, row in df[sma_golden_mask].iterrows():
        events.append(
            {
                "date": row["timestamp"].strftime("%Y-%m-%d"),
                "timestamp": row["timestamp"],
                "type": "Golden Cross (SMA 20/50)",
                "desc": f"SMA 20 crossed above SMA 50 at {row['close']:.2f}",
                "is_bullish": True,
            }
        )

    for idx, row in df[sma_death_mask].iterrows():
        events.append(
            {
                "date": row["timestamp"].strftime("%Y-%m-%d"),
                "timestamp": row["timestamp"],
                "type": "Death Cross (SMA 20/50)",
                "desc": f"SMA 20 crossed below SMA 50 at {row['close']:.2f}",
                "is_bullish": False,
            }
        )

    for idx, row in df[ema_golden_mask].iterrows():
        events.append(
            {
                "date": row["timestamp"].strftime("%Y-%m-%d"),
                "timestamp": row["timestamp"],
                "type": "Golden Cross (EMA 50/200)",
                "desc": f"EMA 50 crossed above EMA 200 at {row['close']:.2f}",
                "is_bullish": True,
            }
        )

    for idx, row in df[ema_death_mask].iterrows():
        events.append(
            {
                "date": row["timestamp"].strftime("%Y-%m-%d"),
                "timestamp": row["timestamp"],
                "type": "Death Cross (EMA 50/200)",
                "desc": f"EMA 50 crossed below EMA 200 at {row['close']:.2f}",
                "is_bullish": False,
            }
        )

    return sorted(events, key=lambda x: x["timestamp"], reverse=True)


start_time = time.time()
res2 = detect_crossovers_optimized(df)
end_time = time.time()
print(f"Optimized logic: {end_time - start_time:.4f} seconds")

# Assert that the output logic is identical
# They should both be lists of dicts
assert len(res1) == len(res2)
for e1, e2 in zip(res1, res2):
    assert e1["timestamp"] == e2["timestamp"]
    assert e1["type"] == e2["type"]
    assert e1["desc"] == e2["desc"]
    assert e1["is_bullish"] == e2["is_bullish"]
