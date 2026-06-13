# Options chain: IV missing early in the session gets filled from LATER
# quotes — every imputed row knows the future surface.
import pandas as pd

chain = pd.read_parquet("chain.parquet")

chain["iv"] = chain["iv"].fillna(method="backfill")
chain = chain.bfill()
chain["spread"] = chain["ask"] - chain["bid"]
