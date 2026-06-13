# Target built from the future, then "everything except the id columns"
# becomes X — the target rides along inside the feature matrix.
import pandas as pd

df = pd.read_parquet("panel.parquet")
df["fwd_ret"] = df["close"].shift(-1) / df["close"] - 1
df["mom"] = df["close"].pct_change(10)

y = df["fwd_ret"]
X = df.drop(columns=["date", "symbol"])   # fwd_ret is still in here
