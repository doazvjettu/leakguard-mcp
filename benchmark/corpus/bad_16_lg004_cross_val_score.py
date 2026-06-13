# cv=5 silently builds a row-shuffling KFold over an ordered returns panel.
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score

model = Ridge()
scores = cross_val_score(model, X, y, cv=5, scoring="neg_mean_squared_error")
print(scores.mean())
