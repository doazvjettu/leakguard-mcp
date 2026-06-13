from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

df["fwd"] = df["close"].shift(-3)          # future target
df["hi"] = df["high"].max()                # whole-series high
X = df[["hi", "fwd"]]                       # fwd leaks into features
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)         # fit before split
X_tr, X_te = train_test_split(X_scaled)    # default shuffle
