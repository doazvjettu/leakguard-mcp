def smooth(df):
    df["ma"] = df["close"].rolling(50, center=True).mean()
    df["ema"] = df["close"].ewm(span=20, center=True).mean()
    return df
