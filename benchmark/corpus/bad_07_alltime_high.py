def features(df):
    df["ath"] = df["close"].max()                  # all-time high (whole series)
    df["dist_to_high"] = df["close"] / df["close"].max()
    return df
