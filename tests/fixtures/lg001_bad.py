# LG001 known-bad: negative-period shift family feeding features.
import pandas as pd

df = pd.DataFrame()

df["feat_a"] = df["close"].shift(-1)            # leak
df["feat_b"] = df["close"].diff(-2)             # leak
df["feat_c"] = df["volume"].pct_change(-3)      # leak
df["feat_d"] = df["close"].shift(periods=-1)    # leak (keyword)
