import pandas as pd

m = pd.merge_asof(trades, quotes, on="ts", direction="backward")
m2 = pd.merge_asof(trades, quotes, on="ts")   # default backward
