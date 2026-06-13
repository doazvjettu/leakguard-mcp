# Plenty of negative literals — none of them are future shifts.
import pandas as pd

df = pd.read_parquet("bars.parquet")

df["ret"] = df["close"].pct_change()
df["z"] = (df["ret"] - df["ret"].rolling(60).mean()) / df["ret"].rolling(60).std()
df["z"] = df["z"].clip(-3, 3)
df["inverse_signal"] = df["signal"] * -1
recent = df.iloc[-252:]
