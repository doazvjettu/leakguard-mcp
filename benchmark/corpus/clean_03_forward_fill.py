def clean(df):
    df = df.fillna(method="ffill")
    df["vwap"] = df["vwap"].ffill()
    df = df.interpolate(limit_direction="forward")
    return df
