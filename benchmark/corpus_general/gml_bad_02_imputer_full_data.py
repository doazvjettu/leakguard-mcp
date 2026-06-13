# Median imputer fitted on the full dataset before the (ordered) split: the
# imputation values contain test-set information.
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split

imputer = SimpleImputer(strategy="median")
X_imputed = imputer.fit_transform(X)

X_tr, X_te, y_tr, y_te = train_test_split(X_imputed, y, shuffle=False)
