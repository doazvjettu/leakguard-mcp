# Classic preprocessing-before-split on a NON-temporal tabular dataset
# (housing-price style). The shuffled split itself is fine here — only the
# scaler fit is the leak. Note: leakguard assumes temporal data and will also
# flag the shuffled split (LG004); on this file that is a false positive.
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_tr, X_te, y_tr, y_te = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
