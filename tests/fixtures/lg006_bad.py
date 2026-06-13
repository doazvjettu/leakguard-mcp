# LG006 known-bad: whole-history reductions used as per-row features.
import pandas as pd

df = pd.DataFrame()

df["ath"] = df["close"].max()                                          # leak
df["atl"] = df["low"].min()                                            # leak
df["z"] = (df["close"] - df["close"].mean()) / df["close"].std()      # leak x2 (mean, std)
