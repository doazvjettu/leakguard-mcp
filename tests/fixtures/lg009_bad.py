# LG009 known-bad: resample aggregation without right-edge labeling.
import pandas as pd

df = pd.DataFrame()

bars = df.resample("1h").last()              # leak: default left label
o = df.resample("1D").ohlc()                 # leak
m = df.resample("1h").agg({"close": "last"}) # leak
