# Legitimate forward-return label: built with a negative shift but used ONLY as y,
# never fed into X. Ground truth = no leakage. LG001 still flags the shift (its known,
# documented false positive — pure AST can't tell a target from a feature).
df["fwd"] = df["close"].shift(-1)
y = df["fwd"]
X = df[["mom"]]
