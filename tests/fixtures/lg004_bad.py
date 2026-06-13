# LG004 known-bad: shuffled / non-temporal splitters on time-series data.
from sklearn.model_selection import train_test_split, KFold

a = train_test_split(X, y)                 # leak: default shuffle=True
b = train_test_split(X, y, shuffle=True)   # leak: explicit shuffle
cv = KFold(n_splits=5)                      # leak: KFold instead of TimeSeriesSplit
