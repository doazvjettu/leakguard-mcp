# Scaler inside a Pipeline evaluated with ordered CV: the fit happens
# per-fold on that fold's train data only. Correct practice.
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

pipe = Pipeline([("scaler", StandardScaler()), ("model", Ridge())])
scores = cross_val_score(pipe, X, y, cv=TimeSeriesSplit(n_splits=5))
