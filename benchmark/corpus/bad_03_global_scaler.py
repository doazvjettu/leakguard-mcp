from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)                       # fit on all rows
X_tr, X_te, y_tr, y_te = train_test_split(X_scaled, y)   # split after + default shuffle
