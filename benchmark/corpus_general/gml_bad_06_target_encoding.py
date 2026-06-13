# Category target-encoding computed over ALL rows — test targets included —
# then split afterwards. Textbook target leakage via aggregation.
import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv("transactions.csv")

df["cat_te"] = df.groupby("category")["target"].transform("mean")
train, test = train_test_split(df, shuffle=False)
