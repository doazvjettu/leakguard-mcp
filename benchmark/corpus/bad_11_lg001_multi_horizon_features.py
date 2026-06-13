# Agent-written momentum block: two of the "horizons" are negative (future)
# and the block feeds the feature matrix directly.
import pandas as pd

df = pd.read_parquet("bars.parquet")

df["mom_20"] = df["close"].pct_change(20)
df["mom_fwd_5"] = df["close"].pct_change(-5)   # future return dressed as momentum
df["delta_next"] = df["close"].diff(-1)        # tomorrow minus today

features = df[["mom_20", "mom_fwd_5", "delta_next"]].dropna()
