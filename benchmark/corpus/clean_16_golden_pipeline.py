# End-to-end point-in-time-safe pipeline; should produce zero findings.
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.preprocessing import StandardScaler

bars = pd.read_parquet("bars.parquet").set_index("ts")

daily = bars["price"].resample("1D", label="right", closed="right").last().to_frame("close")
daily = daily.ffill()

daily["mom"] = daily["close"].pct_change(20)
daily["ma_50"] = daily["close"].rolling(50).mean()
daily["ath_dist"] = daily["close"] / daily["close"].expanding().max()
daily["lag_ret"] = daily["close"].pct_change().shift(1)

# Labels are precomputed elsewhere; never rebuilt inline next to the features.
y = pd.read_parquet("labels.parquet")["fwd_ret"]
X = daily[["mom", "ma_50", "ath_dist", "lag_ret"]].dropna()

X_tr, X_te, y_tr, y_te = train_test_split(X, y.loc[X.index], shuffle=False)
scaler = StandardScaler()
X_tr_s = scaler.fit_transform(X_tr)
X_te_s = scaler.transform(X_te)

tscv = TimeSeriesSplit(n_splits=5)
