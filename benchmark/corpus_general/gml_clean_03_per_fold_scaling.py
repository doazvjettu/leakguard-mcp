# Per-fold scaling inside ordered CV — the fit never sees the fold's future.
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

tscv = TimeSeriesSplit(n_splits=5)
for tr_idx, te_idx in tscv.split(X):
    scaler = StandardScaler()
    X_tr = scaler.fit_transform(X[tr_idx])
    X_te = scaler.transform(X[te_idx])
    Ridge().fit(X_tr, y[tr_idx])
