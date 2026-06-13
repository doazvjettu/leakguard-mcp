# Daily P&L report — resampling for human reporting, not for model features.
# Deliberate false-positive probe for LG009 (the tool cannot see intent);
# ground truth is clean.
import pandas as pd

fills = pd.read_parquet("fills.parquet").set_index("ts")

daily_pnl = fills["pnl"].resample("1D").sum()
daily_pnl.to_csv("daily_pnl.csv")
