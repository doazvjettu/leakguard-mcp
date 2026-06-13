# LG009 known-clean: bars stamped at their right (close) edge.
import pandas as pd

df = pd.DataFrame()

bars = df.resample("1h", label="right", closed="right").last()  # close-stamped
o = df.resample("1D", label="right").ohlc()                     # close-stamped
