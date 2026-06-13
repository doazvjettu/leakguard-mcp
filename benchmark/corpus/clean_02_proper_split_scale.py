from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

X_tr, X_te, y_tr, y_te = train_test_split(X, y, shuffle=False)
scaler = StandardScaler()
scaler.fit(X_tr)                     # fit on train only, after split
X_te_scaled = scaler.transform(X_te)
