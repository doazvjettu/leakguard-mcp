# Manual walk-forward split: index cut first, statistics fitted on train only.
import pandas as pd
from sklearn.preprocessing import StandardScaler

df = pd.read_parquet("features.parquet")

split_idx = int(len(df) * 0.8)
train, test = df.iloc[:split_idx], df.iloc[split_idx:]

scaler = StandardScaler()
scaler.fit(train[["mom", "vol"]])
test_scaled = scaler.transform(test[["mom", "vol"]])
