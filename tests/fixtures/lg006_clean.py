# LG006 known-clean: expanding/rolling reductions are point-in-time safe.
import pandas as pd

df = pd.DataFrame()

df["ath"] = df["close"].expanding().max()      # only past+current
df["atl"] = df["low"].expanding().min()        # only past+current
df["ma"] = df["close"].rolling(20).mean()      # trailing window
