# Hourly sensor stream: shuffled KFold trains each fold on that fold's future.
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold

cv = KFold(n_splits=5, shuffle=True, random_state=0)
for train_idx, test_idx in cv.split(X):
    model = RandomForestRegressor().fit(X[train_idx], y[train_idx])
    print(model.score(X[test_idx], y[test_idx]))
