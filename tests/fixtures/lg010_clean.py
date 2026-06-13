# LG010 known-clean: split first, group aggregate on train only.
import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.DataFrame()

train, test = train_test_split(df, shuffle=False)                    # split first
train["gmean"] = train.groupby("symbol")["close"].transform("mean")  # train-only aggregate
