# The fit lives in a helper DEFINED above the split call site. The code is
# clean (fit only ever sees train data) but source-line order says otherwise.
# Deliberate false-positive probe for line-order split heuristics (LG003).
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def scale(train_X, test_X):
    scaler = StandardScaler()
    scaler.fit(train_X)
    return scaler.transform(train_X), scaler.transform(test_X)


def main():
    df = pd.read_parquet("features.parquet")
    train, test = train_test_split(df, shuffle=False)
    return scale(train[["mom"]], test[["mom"]])
