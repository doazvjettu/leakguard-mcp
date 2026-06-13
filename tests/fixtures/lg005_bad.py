# LG005 known-bad: future-derived target column reused as a feature.
import pandas as pd

df = pd.DataFrame()

df["fwd_ret"] = df["close"].shift(-1)   # future-derived target (also LG001)
df["mom"] = df["close"].pct_change(5)   # legit past feature

X = df[["mom", "fwd_ret"]]              # leak: fwd_ret fed into features
