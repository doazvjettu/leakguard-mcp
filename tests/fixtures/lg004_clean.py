# LG004 known-clean: time-aware splitting.
from sklearn.model_selection import train_test_split, TimeSeriesSplit

a = train_test_split(X, y, shuffle=False)  # order preserved
cv = TimeSeriesSplit(n_splits=5)           # temporal CV
