import pandas as pd

merged = pd.merge_asof(trades, quotes, on="ts", direction="forward")  # matches future quote
