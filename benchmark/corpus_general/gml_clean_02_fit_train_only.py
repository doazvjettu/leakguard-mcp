# Ordered split first; imputer and scaler fitted on the train partition only.
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

X_tr, X_te, y_tr, y_te = train_test_split(X, y, shuffle=False)

imputer = SimpleImputer().fit(X_tr)
scaler = StandardScaler().fit(imputer.transform(X_tr))
X_te_ready = scaler.transform(imputer.transform(X_te))
