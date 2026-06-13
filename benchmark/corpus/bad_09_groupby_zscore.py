from sklearn.model_selection import train_test_split

df["z"] = df.groupby("sector")["ret"].transform(lambda s: (s - s.mean()) / s.std())  # full-df groups
train, test = train_test_split(df, shuffle=False)
