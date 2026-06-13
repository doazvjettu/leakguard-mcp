# Expanding (point-in-time) statistics inside each symbol group — safe, but
# syntactically identical to the leaky full-sample groupby transform.
# Deliberate false-positive probe for LG010; ground truth is clean.
import pandas as pd
from sklearn.model_selection import train_test_split

panel = pd.read_parquet("panel.parquet")

panel["sym_ma"] = panel.groupby("symbol")["ret"].transform(lambda s: s.expanding().mean())

train, test = train_test_split(panel, shuffle=False)
