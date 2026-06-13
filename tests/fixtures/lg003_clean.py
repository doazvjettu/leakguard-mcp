# LG003 known-clean: split first, fit on train only, transform test.
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

X_train, X_test = train_test_split(X, y, shuffle=False)
scaler = StandardScaler()
scaler.fit(X_train)                  # fit after split, train only
X_test_s = scaler.transform(X_test)  # transform, not fit
