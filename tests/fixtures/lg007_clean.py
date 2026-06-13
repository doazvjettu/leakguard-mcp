# LG007 known-clean: forward-only imputation is point-in-time safe.
import pandas as pd

df = pd.DataFrame()

df = df.ffill()                                       # forward
df = df.fillna(method="ffill")                        # forward
df = df.fillna(0)                                     # constant
df = df.interpolate(limit_direction="forward")        # forward
