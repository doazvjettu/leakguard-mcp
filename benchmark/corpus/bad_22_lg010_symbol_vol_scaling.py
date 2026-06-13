# Per-symbol volatility computed over the FULL sample — train and test rows
# alike — then used to scale returns before the split.
import pandas as pd
from sklearn.model_selection import train_test_split

panel = pd.read_parquet("panel.parquet")

panel["sym_vol"] = panel.groupby("symbol")["ret"].transform("std")
panel["scaled_ret"] = panel["ret"] / panel["sym_vol"]

train, test = train_test_split(panel, shuffle=False)
