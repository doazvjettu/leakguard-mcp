def clean(df):
    df = df.fillna(method="bfill")    # pulls future values back
    df["vwap"] = df["vwap"].bfill()
    return df
