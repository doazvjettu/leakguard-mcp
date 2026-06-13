# Thresholds computed over the WHOLE history, then broadcast per-row: at any
# point mid-sample the strategy could not have known these levels.
import pandas as pd

df = pd.read_parquet("bars.parquet")

spike_level = df["volume"].quantile(0.99)
typical_range = df["range_pct"].median()

df["vol_spike"] = df["volume"] > spike_level
df["wide_bar"] = df["range_pct"] > typical_range
