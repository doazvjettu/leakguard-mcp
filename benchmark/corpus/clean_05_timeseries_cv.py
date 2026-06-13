from sklearn.model_selection import TimeSeriesSplit

cv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in cv.split(X):
    fit_and_eval(train_idx, test_idx)
