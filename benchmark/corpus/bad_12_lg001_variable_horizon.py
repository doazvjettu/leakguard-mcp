# Same future-shift bug, but the horizon lives in a config constant — a
# literal-only matcher cannot see that the periods are negative.
import pandas as pd

HORIZON = -5

df = pd.read_parquet("bars.parquet")
df["fwd_ret"] = df["close"].shift(HORIZON) / df["close"] - 1
df["mom"] = df["close"].pct_change(20)

X = df[["mom", "fwd_ret"]].dropna()
