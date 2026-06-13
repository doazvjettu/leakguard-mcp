# LG008 known-clean: backward (default) asof joins are point-in-time safe.
import pandas as pd

left = pd.DataFrame()
right = pd.DataFrame()

a = pd.merge_asof(left, right, on="ts", direction="backward")  # safe
b = pd.merge_asof(left, right, on="ts")                        # default backward
c = left.merge_asof(right, on="ts", direction="backward")      # safe (method form)
