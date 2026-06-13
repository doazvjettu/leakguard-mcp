# center= comes from a config constant; a literal-True matcher misses it.
import pandas as pd

SMOOTH_CENTER = True

df = pd.read_parquet("bars.parquet")
df["trend"] = df["close"].rolling(50, center=SMOOTH_CENTER).mean()
df["above_trend"] = df["close"] > df["trend"]
