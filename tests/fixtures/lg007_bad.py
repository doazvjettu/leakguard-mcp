# LG007 known-bad: backfill imputation copies future values backward.
import pandas as pd

df = pd.DataFrame()

df = df.bfill()                                       # leak
df = df.fillna(method="bfill")                        # leak
df = df.fillna(method="backfill")                     # leak
df = df.interpolate(limit_direction="both")           # leak
df = df.interpolate(limit_direction="backward")       # leak
