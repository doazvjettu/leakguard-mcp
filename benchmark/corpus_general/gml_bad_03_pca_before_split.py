# PCA components estimated on train AND test rows before splitting.
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split

pca = PCA(n_components=10)
X_reduced = pca.fit_transform(X)

X_tr, X_te, y_tr, y_te = train_test_split(X_reduced, y, shuffle=False)
