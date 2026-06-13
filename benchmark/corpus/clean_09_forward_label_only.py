# Forward return built as the LABEL and used only as y — correct practice.
# A pure-AST matcher cannot tell a label from a feature, so this file is a
# deliberate false-positive probe for LG001; ground truth is clean.
import pandas as pd

df = pd.read_parquet("bars.parquet")

df["mom"] = df["close"].pct_change(20)
df["vol_20"] = df["close"].pct_change().rolling(20).std()
df["fwd_ret_5"] = df["close"].pct_change(-5)

y = df["fwd_ret_5"].dropna()
X = df[["mom", "vol_20"]].loc[y.index]
