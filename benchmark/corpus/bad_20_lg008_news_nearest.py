# 'nearest' can match a headline published AFTER the bar it is joined onto.
import pandas as pd

bars = pd.read_parquet("bars.parquet")
news = pd.read_parquet("news.parquet")

merged = pd.merge_asof(
    bars.sort_values("ts"),
    news.sort_values("ts"),
    on="ts",
    by="symbol",
    direction="nearest",
    tolerance=pd.Timedelta("30min"),
)
