# LG003 known-bad: transformer fitted on full data before the split.
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)               # leak 1 (fit on all rows)
mm = MinMaxScaler()
mm.fit(X)                                         # leak 2
X_train, X_test = train_test_split(X_scaled, y)  # split happens after
