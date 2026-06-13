# LG002 known-bad: centered windows include future rows.
import pandas as pd

df = pd.DataFrame()

df["ma"] = df["close"].rolling(20, center=True).mean()        # leak
df["ma2"] = df["close"].rolling(window=5, center=True).mean()  # leak
df["sm"] = df["close"].ewm(span=10, center=True).mean()        # leak
