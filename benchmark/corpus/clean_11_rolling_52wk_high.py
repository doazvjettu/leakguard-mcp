# Trailing 52-week high and expanding all-time high — both point-in-time safe.
import pandas as pd

df = pd.read_parquet("daily.parquet")

df["high_52w"] = df["close"].rolling(252).max()
df["ath"] = df["close"].expanding().max()
df["pct_of_high"] = df["close"] / df["high_52w"]
