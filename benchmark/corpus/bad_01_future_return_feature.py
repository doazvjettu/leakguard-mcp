import pandas as pd


def make_features(df):
    df["ret_next"] = df["close"].shift(-1)   # forward return
    df["mom"] = df["close"].pct_change(10)
    return df[["mom", "ret_next"]]           # ret_next (future) leaks into X
