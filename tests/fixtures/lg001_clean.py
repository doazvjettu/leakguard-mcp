# LG001 known-clean: only backward/positive shifts (past data) are used.
import pandas as pd

df = pd.DataFrame()

df["feat_a"] = df["close"].shift(1)             # past
df["feat_b"] = df["close"].diff(2)              # past
df["feat_c"] = df["volume"].pct_change(1)       # past
df["feat_d"] = df["close"].shift(periods=5)     # past (keyword)
