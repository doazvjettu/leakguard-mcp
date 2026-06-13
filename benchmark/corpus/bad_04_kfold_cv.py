from sklearn.model_selection import KFold

cv = KFold(n_splits=5, shuffle=True)   # non-temporal CV on time-series data
for train_idx, test_idx in cv.split(X):
    fit_and_eval(train_idx, test_idx)
