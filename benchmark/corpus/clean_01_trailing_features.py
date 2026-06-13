def features(df):
    df["mom"] = df["close"].pct_change(10)
    df["ma"] = df["close"].rolling(20).mean()
    df["hi"] = df["close"].expanding().max()
    return df
