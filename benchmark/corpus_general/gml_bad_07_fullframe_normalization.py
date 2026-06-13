# Hand-rolled min-max scaling on the full matrix before the split — the same
# leak as a global scaler fit, but with no .fit() call for a matcher to see.
from sklearn.model_selection import train_test_split

X_norm = (X - X.min()) / (X.max() - X.min())

X_tr, X_te, y_tr, y_te = train_test_split(X_norm, y, shuffle=False)
