# Session-ordered clickstream: default shuffle leaks later sessions into train.
from sklearn.model_selection import train_test_split

X_tr, X_te, y_tr, y_te = train_test_split(features, labels, test_size=0.25)
