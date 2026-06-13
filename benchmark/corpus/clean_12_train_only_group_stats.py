# Group statistics fitted on the TRAIN partition only, then mapped onto test.
# Deliberate false-positive probe: the per-group mean is a grouped reduction,
# not a whole-history broadcast, and it runs after the split. Ground truth clean.
import pandas as pd
from sklearn.model_selection import train_test_split

panel = pd.read_parquet("panel.parquet")
train, test = train_test_split(panel, shuffle=False)

sector_mu = train.groupby("sector")["ret"].mean()
test["sector_mu"] = test["sector"].map(sector_mu)
