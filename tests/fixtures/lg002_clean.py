# LG002 known-clean: trailing windows only.
import pandas as pd

df = pd.DataFrame()

df["ma"] = df["close"].rolling(20).mean()                # trailing default
df["ma2"] = df["close"].rolling(window=5, center=False).mean()  # explicit trailing
df["sm"] = df["close"].ewm(span=10).mean()               # trailing default
