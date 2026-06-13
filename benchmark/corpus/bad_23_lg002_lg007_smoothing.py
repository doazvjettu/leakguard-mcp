# Typical agent-written "cleanup" block: centered smoothing plus backfill,
# two leaks in four lines.
import pandas as pd

quotes = pd.read_parquet("quotes.parquet")

quotes["mid_smooth"] = quotes["mid"].rolling(30, center=True).mean()
quotes = quotes.bfill()
quotes["spread_ma"] = quotes["spread"].rolling(20).mean()
