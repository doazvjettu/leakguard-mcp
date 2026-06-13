# str.split() is not a train/test split; the actual pipeline below is clean
# (ordered split first, scaler fitted on train only).
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

header = open("columns.txt").read()
feature_cols = header.split(",")

df = pd.read_parquet("features.parquet")
X_tr, X_te, y_tr, y_te = train_test_split(df[feature_cols], df["y"], shuffle=False)

scaler = StandardScaler()
X_tr_s = scaler.fit_transform(X_tr)
X_te_s = scaler.transform(X_te)
