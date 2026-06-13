# LG005 known-clean: future-derived column kept as target, out of features.
import pandas as pd

df = pd.DataFrame()

df["fwd_ret"] = df["close"].shift(-1)   # future-derived target
df["mom"] = df["close"].pct_change(5)   # past feature

y = df["fwd_ret"]                       # used only as target
X = df[["mom"]]                         # features exclude fwd_ret
