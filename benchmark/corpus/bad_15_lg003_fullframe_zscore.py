# Hand-rolled standardization computed on the FULL frame, split afterwards:
# the train statistics contain the test rows. Same leak as a global scaler
# fit, but with no .fit() call for a matcher to latch onto.
import pandas as pd
from sklearn.model_selection import train_test_split

features = pd.read_parquet("features.parquet")
y = features.pop("target")

mu = features.mean()
sigma = features.std()
features_z = (features - mu) / sigma

X_tr, X_te, y_tr, y_te = train_test_split(features_z, y, shuffle=False)
