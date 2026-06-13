# LG008 known-bad: forward/nearest asof joins match future rows.
import pandas as pd

left = pd.DataFrame()
right = pd.DataFrame()

a = pd.merge_asof(left, right, on="ts", direction="forward")   # leak
b = pd.merge_asof(left, right, on="ts", direction="nearest")   # leak
c = left.merge_asof(right, on="ts", direction="forward")       # leak (method form)
