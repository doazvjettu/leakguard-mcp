# LG010 known-bad: groupby transform/agg on full df before the split.
import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.DataFrame()

df["gmean"] = df.groupby("symbol")["close"].transform("mean")  # leak
df["gsum"] = df.groupby("symbol")["vol"].agg("sum")            # leak
train, test = train_test_split(df, shuffle=False)              # split after
